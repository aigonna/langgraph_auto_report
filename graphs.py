# !/usr/bin/env python
# -*-coding:utf-8 -*-
# File       : graphs.py
# Time       ：2025/6/30 20:53
# Author     ：aigonna
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from state import State
from nodes import (report_node, execute_node, create_planner_node, update_planner_node)


def _build_base_graph() -> StateGraph:
    """
    Build and return the base state graph with all nodes and edges.
    """
    builder = StateGraph(State)
    builder.add_edge(START, 'create_planner')
    builder.add_node('create_planner', create_planner_node)
    builder.add_node('update_planner', update_planner_node)
    builder.add_node('execute', execute_node)
    builder.add_node('report', report_node)
    builder.add_edge("report", END)
    return builder

def build_graph_with_memory() -> StateGraph:
    """Build and return the agent workflow graph with memory."""
    memory = MemorySaver()
    builder = _build_base_graph()
    return builder.compile(checkpointer=memory)

def build_graph():
    """Build and return the agent workflow graph without memory."""
    builder = _build_base_graph()
    return builder.compile()


graph = build_graph()
inputs = {"user_message": "对所给csv数据进行分析，生成分析报告，文档路径为./data/China Automobile Sales Data.csv",
          "plan": None,
          "observations": [],
          "final_report": "",
          "task_folder": ""}

graph.invoke(inputs, {"recursion_limit":100})