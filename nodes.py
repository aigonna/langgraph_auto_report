# !/usr/bin/env python
# -*-coding:utf-8 -*-
# File       : nodes.py
# Time       ：2025/6/30 20:37
# Author     ：aigonna
import os
import json
from loguru import logger
from typing import Annotated, Literal
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.types import Command, interrupt
from langchain_deepseek import ChatDeepSeek
from langchain.chat_models import ChatOpenAI
from state import State
from prompts import (PLAN_SYSTEM_PROMPT, PLAN_CREATE_PROMPT,
                     EXECUTE_SYSTEM_PROMPT, EXECUTION_PROMPT, REPORT_SYSTEM_PROMPT)
from tools import create_file, create_task_folder, send_messages, shell_exec, str_replace
from dotenv import load_dotenv
load_dotenv('.env')
api_key = os.getenv("deepseek")

# LLM配置
llm = ChatDeepSeek(
    model="deepseek-chat",
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

# llm = ChatOpenAI(temperature=0.7, model_name="gpt-3.5-turbo")

def extract_json(text):
    if '```json' not in text:
        return text
    text = text.split('```json')[1].split('```')[0].strip()
    return text

def extract_answer(text):
    return text

def create_planner_node(state: State):
    logger.info("***正在运行Create Planner node***")
    
    # Create task folder first if not already created
    if not state.get('task_folder'):
        task_folder_result = create_task_folder.invoke({"user_message": state['user_message']})
        if "task_folder" in task_folder_result:
            task_folder = task_folder_result["task_folder"]
            logger.info(f"Created task folder: {task_folder}")
        else:
            task_folder = ""
            logger.error(f"Failed to create task folder: {task_folder_result}")
    else:
        task_folder = state['task_folder']
    
    messages = [SystemMessage(content=PLAN_SYSTEM_PROMPT), HumanMessage(content=PLAN_CREATE_PROMPT.format(user_message = state['user_message']))]
    response = llm.invoke(messages)
    response = response.model_dump_json(indent=4, exclude_none=True)
    response = json.loads(response)
    plan = json.loads(extract_json(extract_answer(response['content'])))
    state['messages'] += [AIMessage(content=json.dumps(plan, ensure_ascii=False))]
    return Command(goto="execute", update={"plan": plan, "task_folder": task_folder})

def execute_node(state: State):
    logger.info("***正在运行execute_node***")
  
    plan = state['plan']
    steps = plan['steps']
    current_step = None
    current_step_index = 0
    
    # 获取第一个未完成STEP
    for i, step in enumerate(steps):
        status = step['status']
        if status == 'pending':
            current_step = step
            current_step_index = i
            break
        
    logger.info(f"当前执行STEP:{current_step}")
    
    # 如果没有待执行的步骤，跳转到report节点
    if current_step is None:
        logger.info("所有步骤已完成，跳转到report节点")
        return Command(goto='report')
    
    # 过滤掉ToolMessage，只保留SystemMessage、HumanMessage和AIMessage
    filtered_observations = [msg for msg in state['observations'] if not isinstance(msg, ToolMessage)]
    messages = filtered_observations + [SystemMessage(content=EXECUTE_SYSTEM_PROMPT), HumanMessage(content=EXECUTION_PROMPT.format(user_message=state['user_message'], step=current_step['description']))]
    
    tool_result = None
    while True:
        response = llm.bind_tools([create_file, str_replace, shell_exec]).invoke(messages)
        response = response.model_dump_json(indent=4, exclude_none=True)
        response = json.loads(response)
        tools = {"create_file": create_file, "str_replace": str_replace, "shell_exec": shell_exec}     
        if response['tool_calls']:
            # 先添加AI响应消息
            messages += [AIMessage(content=response['content'], tool_calls=response['tool_calls'])]
            for tool_call in response['tool_calls']:
                tool_name = tool_call['name']
                tool_args = tool_call['args']
                
                # Add task_folder to create_file calls
                if tool_name == 'create_file' and state.get('task_folder'):
                    tool_args['task_folder'] = state['task_folder']
                
                tool_result = tools[tool_name].invoke(tool_args)
                logger.info(f"tool_name:{tool_name},tool_args:{tool_args}\ntool_result:{tool_result}")
                messages += [ToolMessage(content=f"tool_name:{tool_name},tool_args:{tool_args}\ntool_result:{tool_result}", tool_call_id=tool_call['id'])]
        
        elif '<tool_call>' in response['content']:
            # DeepSeek 使用标准tool_calls格式，跳过手动解析
            logger.info("检测到<tool_call>标签，但DeepSeek应该使用标准tool_calls格式")
            break
        else:    
            break
        
    logger.info(f"当前STEP执行总结:{extract_answer(response['content'])}")
    
    # 标记当前步骤为已完成
    current_step['status'] = 'completed'
    
    state['messages'] += [AIMessage(content=extract_answer(response['content']))]
    # 只添加执行总结到observations，不添加ToolMessage（避免格式问题）
    state['observations'] += [AIMessage(content=extract_answer(response['content']))]
    
    # 检查是否还有未完成的步骤
    remaining_pending_steps = [step for step in steps if step['status'] == 'pending']
    
    if remaining_pending_steps:
        logger.info(f"还有 {len(remaining_pending_steps)} 个步骤待执行，继续执行")
        return Command(goto='execute', update={'plan': plan})
    else:
        logger.info("所有步骤已完成，跳转到report节点")
        return Command(goto='report', update={'plan': plan})
    

    
def report_node(state: State):
    """Report node that write a final report."""
    logger.info("***正在运行report_node***")
    
    observations = state.get("observations")
    # 过滤掉ToolMessage，只保留SystemMessage、HumanMessage和AIMessage
    filtered_observations = [msg for msg in observations if not isinstance(msg, ToolMessage)] if observations else []
    messages = filtered_observations + [SystemMessage(content=REPORT_SYSTEM_PROMPT)]
    
    while True:
        response = llm.bind_tools([create_file, shell_exec]).invoke(messages)
        response = response.model_dump_json(indent=4, exclude_none=True)
        response = json.loads(response)
        tools = {"create_file": create_file, "shell_exec": shell_exec} 
        if response['tool_calls']:    
            for tool_call in response['tool_calls']:
                tool_name = tool_call['name']
                tool_args = tool_call['args']
                
                # Add task_folder to create_file calls
                if tool_name == 'create_file' and state.get('task_folder'):
                    tool_args['task_folder'] = state['task_folder']
                
                tool_result = tools[tool_name].invoke(tool_args)
                logger.info(f"tool_name:{tool_name},tool_args:{tool_args}\ntool_result:{tool_result}")
                messages += [ToolMessage(content=f"tool_name:{tool_name},tool_args:{tool_args}\ntool_result:{tool_result}", tool_call_id=tool_call['id'])]
        else:
            break
            
    logger.info("报告生成完成")
    return {"final_report": response['content']}