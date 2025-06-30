# !/usr/bin/env python
# -*-coding:utf-8 -*-
# File       : state.py
# Time       ：2025/6/30 18:00
# Author     ：aigonna
from langgraph.graph import MessagesState
from typing import Optional, List, Dict, Literal
from enum import Enum
from pydantic import BaseModel, Field

class Step(BaseModel):
    title: str = ""
    description: str = ""
    status: Literal["pending", "completed"] = "pending"

class Plan(BaseModel):
    goal: str = ""
    thought: str = ""
    steps: List[Step] = []

class State(MessagesState):
    user_message: str = ""
    plan: Plan
    observations: List = []
    final_report: str = ""
    task_folder: str = ""  # 存储当前任务的输出文件夹路径

