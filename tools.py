# !/usr/bin/env python
# -*-coding:utf-8 -*-
# File       : tools.py
# Time       ：2025/6/30 18:22
# Author     ：aigonna
from langchain_core.tools import tool
import os
import traceback
import subprocess
import uuid
import re
from datetime import datetime


@tool
def create_task_folder(user_message: str):
    """
    Create a unique task folder based on user message and UUID4.
    :param user_message: The user's original message/question
    :return: The path of the created task folder
    """
    try:
        # Extract keywords from user message for folder naming
        # Remove special characters and keep only letters, numbers, and spaces
        clean_message = re.sub(r'[^\w\s-]', '', user_message.strip())
        # Take first 30 characters and replace spaces with underscores
        folder_name_base = clean_message[:30].replace(' ', '_').replace('　', '_')
        
        # Generate UUID4 for uniqueness
        task_id = str(uuid.uuid4())[:8]  # Use first 8 characters of UUID
        
        # Create timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Combine to create folder name
        folder_name = f"{timestamp}_{folder_name_base}_{task_id}"
        
        # Create the full path
        task_folder_path = os.path.join("output", folder_name)
        full_path = os.path.join(os.getcwd(), task_folder_path)
        
        # Create the directory
        os.makedirs(full_path, exist_ok=True)
        
        return {"messages": f"Successfully created task folder at {full_path}", "task_folder": task_folder_path}
    except Exception as e:
        return {"error": f"Error creating task folder: {str(e)}"}


@tool
def create_file(file_name: str, file_contents: str, task_folder: str = ""):
    """
    Create a new file with the provided contents in the specified task folder.
    :param file_name: name to the file to be created
    :param file_contents: the content to write to the file
    :param task_folder: the task folder path (optional, if not provided will use output/)
    """
    try:
        # Use task folder if provided, otherwise use default output folder
        if task_folder:
            if not task_folder.startswith('output/'):
                task_folder = os.path.join('output', task_folder)
            file_path = os.path.join(os.getcwd(), task_folder, file_name)
        else:
            # Fallback to output folder
            if not file_name.startswith('output/'):
                file_name = os.path.join('output', file_name)
            file_path = os.path.join(os.getcwd(), file_name)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_contents)

        return {"messages": f"Successfully created file at {file_path}."}
    except Exception as e:
        return {"error": f"Error creating file: {str(e)}"}

@tool
def str_replace(file_name: str, old_str: str, new_str: str):
    """
    Replace specific text in a file.
    :param file_name: name to the target file
    :param old_str: Text to be replaced (must appear exactly once)
    :param new_str: Replacement text
    """
    try:
        file_path = os.path.join(os.getcwd(), file_name)
        with open(file_path, 'r') as file:
            content = file.read()
        new_content = content.replace(old_str, new_str, 1)

        with open(file_path, 'w') as file:
            file.write(new_content)

        return {"messages": f"Sucessfully replaced '{old_str} with '{new_str}' in '{file_path}'"}

    except Exception as e:
        return {"error": f"Error replacing '{old_str} with '{new_str}' in {file_path}: {str(e)}"}

@tool
def send_messages(messages: str):
    """
    Send a message to the user.
    :param messages: The message to send to the user.
    """
    return  messages


@tool
def shell_exec(command: str) -> dict:
    """
    在指定shell中执行命令
    :param command: 要执行的shell命令
    :return: dict 包含以下字段：
        - stdout: 命令行的标准输出
        - stderr: 命令行的标准错误
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=os.getcwd(),
            capture_output=True,
            check=False,
            text=True

        )
        return {"messages": {"stdout": result.stdout, "stderr": result.stderr}}
    except Exception as e:
        return {"error": {"stderr": str(e)}}


