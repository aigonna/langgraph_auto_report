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
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from typing import Dict, List, Optional, Union
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


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


# ====== 新增数据分析工具 ======

@tool
def read_csv_data(file_path: str, encoding: str = 'utf-8') -> dict:
    """
    读取CSV文件并返回基本信息
    :param file_path: CSV文件路径
    :param encoding: 文件编码，默认utf-8
    :return: 数据基本信息
    """
    try:
        # 尝试不同编码
        encodings_to_try = [encoding, 'utf-8', 'gbk', 'gb2312', 'latin1']
        df = None
        used_encoding = None
        
        for enc in encodings_to_try:
            try:
                df = pd.read_csv(file_path, encoding=enc)
                used_encoding = enc
                break
            except UnicodeDecodeError:
                continue
        
        if df is None:
            return {"error": "Failed to read CSV with any encoding"}
        
        # 基本信息
        info = {
            "encoding_used": used_encoding,
            "shape": df.shape,
            "columns": df.columns.tolist(),
            "dtypes": df.dtypes.to_dict(),
            "memory_usage": df.memory_usage(deep=True).sum(),
            "null_counts": df.isnull().sum().to_dict(),
            "sample_data": df.head().to_dict(),
            "numerical_columns": df.select_dtypes(include=[np.number]).columns.tolist(),
            "categorical_columns": df.select_dtypes(include=['object']).columns.tolist()
        }
        
        return {"messages": f"Successfully read CSV file with {used_encoding} encoding", "data_info": info}
    except Exception as e:
        return {"error": f"Error reading CSV: {str(e)}"}


@tool
def data_statistics_analysis(file_path: str, task_folder: str = "") -> dict:
    """
    对数据进行全面的统计分析
    :param file_path: 数据文件路径
    :param task_folder: 任务文件夹路径
    :return: 统计分析结果
    """
    try:
        # 读取数据
        df = pd.read_csv(file_path, encoding='utf-8')
        
        # 数值型列统计
        numerical_stats = df.describe()
        
        # 分类型列统计
        categorical_stats = {}
        for col in df.select_dtypes(include=['object']).columns:
            categorical_stats[col] = {
                "unique_count": df[col].nunique(),
                "top_values": df[col].value_counts().head(10).to_dict(),
                "null_count": df[col].isnull().sum()
            }
        
        # 相关性分析
        numerical_df = df.select_dtypes(include=[np.number])
        correlation_matrix = numerical_df.corr()
        
        # 数据质量分析
        quality_analysis = {
            "total_rows": len(df),
            "duplicate_rows": df.duplicated().sum(),
            "missing_data_summary": df.isnull().sum().to_dict(),
            "missing_percentage": (df.isnull().sum() / len(df) * 100).to_dict()
        }
        
        # 保存统计结果
        stats_summary = {
            "numerical_statistics": numerical_stats.to_dict(),
            "categorical_statistics": categorical_stats,
            "correlation_matrix": correlation_matrix.to_dict(),
            "data_quality": quality_analysis
        }
        
        # 生成统计报告文件
        if task_folder:
            stats_file_path = os.path.join(task_folder, "statistical_analysis_summary.json")
            full_stats_path = os.path.join(os.getcwd(), stats_file_path)
            with open(full_stats_path, 'w', encoding='utf-8') as f:
                json.dump(stats_summary, f, ensure_ascii=False, indent=2, default=str)
        
        return {"messages": "Statistical analysis completed successfully", "statistics": stats_summary}
    except Exception as e:
        return {"error": f"Error in statistical analysis: {str(e)}"}


@tool
def create_visualization(file_path: str, chart_type: str, x_column: str, y_column: str = None, 
                        title: str = "Chart", task_folder: str = "", save_name: str = "chart.png") -> dict:
    """
    创建数据可视化图表
    :param file_path: 数据文件路径
    :param chart_type: 图表类型 (bar, line, scatter, hist, box, pie, heatmap)
    :param x_column: X轴列名
    :param y_column: Y轴列名 (可选)
    :param title: 图表标题
    :param task_folder: 任务文件夹路径
    :param save_name: 保存的文件名
    :return: 图表创建结果
    """
    try:
        # 读取数据
        df = pd.read_csv(file_path, encoding='utf-8')
        
        # 设置图表大小和样式
        plt.figure(figsize=(12, 8))
        plt.style.use('default')
        
        if chart_type == "bar":
            if y_column:
                sns.barplot(data=df, x=x_column, y=y_column)
            else:
                df[x_column].value_counts().head(20).plot(kind='bar')
            plt.xticks(rotation=45)
            
        elif chart_type == "line":
            if y_column:
                plt.plot(df[x_column], df[y_column], marker='o')
                plt.xlabel(x_column)
                plt.ylabel(y_column)
            else:
                df[x_column].plot(kind='line')
            
        elif chart_type == "scatter":
            if y_column:
                plt.scatter(df[x_column], df[y_column], alpha=0.6)
                plt.xlabel(x_column)
                plt.ylabel(y_column)
            else:
                return {"error": "Scatter plot requires both x and y columns"}
                
        elif chart_type == "hist":
            plt.hist(df[x_column], bins=30, alpha=0.7, edgecolor='black')
            plt.xlabel(x_column)
            plt.ylabel("Frequency")
            
        elif chart_type == "box":
            if y_column:
                sns.boxplot(data=df, x=x_column, y=y_column)
            else:
                sns.boxplot(data=df, y=x_column)
            plt.xticks(rotation=45)
            
        elif chart_type == "pie":
            value_counts = df[x_column].value_counts().head(10)
            plt.pie(value_counts.values, labels=value_counts.index, autopct='%1.1f%%')
            
        elif chart_type == "heatmap":
            # 数值型列的相关性热力图
            numerical_df = df.select_dtypes(include=[np.number])
            correlation_matrix = numerical_df.corr()
            sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0)
            
        else:
            return {"error": f"Unsupported chart type: {chart_type}"}
        
        plt.title(title, fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        # 保存图表
        if task_folder:
            chart_path = os.path.join(task_folder, save_name)
            full_chart_path = os.path.join(os.getcwd(), chart_path)
        else:
            chart_path = os.path.join("output", save_name)
            full_chart_path = os.path.join(os.getcwd(), chart_path)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(full_chart_path), exist_ok=True)
        plt.savefig(full_chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return {"messages": f"Chart saved successfully at {full_chart_path}", "chart_path": chart_path}
    except Exception as e:
        return {"error": f"Error creating visualization: {str(e)}"}


@tool
def trend_analysis(file_path: str, date_column: str, value_column: str, task_folder: str = "") -> dict:
    """
    进行时间序列趋势分析
    :param file_path: 数据文件路径
    :param date_column: 日期列名
    :param value_column: 数值列名
    :param task_folder: 任务文件夹路径
    :return: 趋势分析结果
    """
    try:
        # 读取数据
        df = pd.read_csv(file_path, encoding='utf-8')
        
        # 转换日期格式
        df[date_column] = pd.to_datetime(df[date_column])
        df = df.sort_values(date_column)
        
        # 计算趋势指标
        df['year'] = df[date_column].dt.year
        df['month'] = df[date_column].dt.month
        df['quarter'] = df[date_column].dt.quarter
        
        # 年度趋势
        yearly_trend = df.groupby('year')[value_column].agg(['sum', 'mean', 'count']).reset_index()
        yearly_growth = yearly_trend['sum'].pct_change() * 100
        
        # 月度趋势
        monthly_trend = df.groupby(['year', 'month'])[value_column].agg(['sum', 'mean', 'count']).reset_index()
        
        # 季度趋势
        quarterly_trend = df.groupby(['year', 'quarter'])[value_column].agg(['sum', 'mean', 'count']).reset_index()
        
        # 计算总体增长率
        first_value = yearly_trend['sum'].iloc[0]
        last_value = yearly_trend['sum'].iloc[-1]
        total_growth = ((last_value - first_value) / first_value) * 100 if first_value != 0 else 0
        
        # 趋势分析结果
        trend_results = {
            "total_growth_rate": total_growth,
            "yearly_growth_rates": yearly_growth.fillna(0).tolist(),
            "yearly_summary": yearly_trend.to_dict('records'),
            "monthly_summary": monthly_trend.to_dict('records'),
            "quarterly_summary": quarterly_trend.to_dict('records'),
            "analysis_period": {
                "start_date": df[date_column].min().strftime('%Y-%m-%d'),
                "end_date": df[date_column].max().strftime('%Y-%m-%d'),
                "total_years": df['year'].nunique()
            }
        }
        
        # 保存趋势分析结果
        if task_folder:
            trend_file_path = os.path.join(task_folder, "trend_analysis_results.json")
            full_trend_path = os.path.join(os.getcwd(), trend_file_path)
            with open(full_trend_path, 'w', encoding='utf-8') as f:
                json.dump(trend_results, f, ensure_ascii=False, indent=2, default=str)
        
        return {"messages": "Trend analysis completed successfully", "trend_analysis": trend_results}
    except Exception as e:
        return {"error": f"Error in trend analysis: {str(e)}"}


@tool
def category_analysis(file_path: str, category_column: str, value_column: str, task_folder: str = "") -> dict:
    """
    进行分类分析，包括排名、占比等
    :param file_path: 数据文件路径
    :param category_column: 分类列名
    :param value_column: 数值列名
    :param task_folder: 任务文件夹路径
    :return: 分类分析结果
    """
    try:
        # 读取数据
        df = pd.read_csv(file_path, encoding='utf-8')
        
        # 按分类汇总
        category_summary = df.groupby(category_column)[value_column].agg([
            'sum', 'mean', 'count', 'std', 'min', 'max'
        ]).reset_index()
        
        # 计算占比
        total_sum = category_summary['sum'].sum()
        category_summary['percentage'] = (category_summary['sum'] / total_sum * 100).round(2)
        
        # 排序
        category_summary = category_summary.sort_values('sum', ascending=False)
        
        # TOP和BOTTOM分析
        top_10 = category_summary.head(10)
        bottom_10 = category_summary.tail(10)
        
        # 分类性能分析
        performance_analysis = {
            "total_categories": len(category_summary),
            "top_10_categories": top_10.to_dict('records'),
            "bottom_10_categories": bottom_10.to_dict('records'),
            "top_3_percentage": top_10.head(3)['percentage'].sum(),
            "concentration_index": (top_10.head(5)['percentage'].sum() / 100),  # 前5名集中度
            "average_performance": category_summary['sum'].mean(),
            "performance_std": category_summary['sum'].std()
        }
        
        # 保存分类分析结果
        if task_folder:
            category_file_path = os.path.join(task_folder, "category_analysis_results.json")
            full_category_path = os.path.join(os.getcwd(), category_file_path)
            with open(full_category_path, 'w', encoding='utf-8') as f:
                json.dump(performance_analysis, f, ensure_ascii=False, indent=2, default=str)
        
        return {"messages": "Category analysis completed successfully", "category_analysis": performance_analysis}
    except Exception as e:
        return {"error": f"Error in category analysis: {str(e)}"}


@tool
def correlation_analysis(file_path: str, task_folder: str = "") -> dict:
    """
    进行相关性分析
    :param file_path: 数据文件路径
    :param task_folder: 任务文件夹路径
    :return: 相关性分析结果
    """
    try:
        # 读取数据
        df = pd.read_csv(file_path, encoding='utf-8')
        
        # 选择数值型列
        numerical_df = df.select_dtypes(include=[np.number])
        
        if numerical_df.empty:
            return {"error": "No numerical columns found for correlation analysis"}
        
        # 计算相关性矩阵
        correlation_matrix = numerical_df.corr()
        
        # 找出强相关关系 (|r| > 0.5)
        strong_correlations = []
        for i in range(len(correlation_matrix.columns)):
            for j in range(i+1, len(correlation_matrix.columns)):
                col1 = correlation_matrix.columns[i]
                col2 = correlation_matrix.columns[j]
                corr_value = correlation_matrix.iloc[i, j]
                if abs(corr_value) > 0.5:
                    strong_correlations.append({
                        "variable1": col1,
                        "variable2": col2,
                        "correlation": round(corr_value, 3),
                        "strength": "strong" if abs(corr_value) > 0.7 else "moderate"
                    })
        
        # 相关性分析结果
        correlation_results = {
            "correlation_matrix": correlation_matrix.to_dict(),
            "strong_correlations": strong_correlations,
            "numerical_columns": numerical_df.columns.tolist(),
            "analysis_summary": {
                "total_variables": len(numerical_df.columns),
                "strong_correlations_count": len(strong_correlations),
                "max_correlation": correlation_matrix.abs().max().max(),
                "mean_correlation": correlation_matrix.abs().mean().mean()
            }
        }
        
        # 保存相关性分析结果
        if task_folder:
            corr_file_path = os.path.join(task_folder, "correlation_analysis_results.json")
            full_corr_path = os.path.join(os.getcwd(), corr_file_path)
            with open(full_corr_path, 'w', encoding='utf-8') as f:
                json.dump(correlation_results, f, ensure_ascii=False, indent=2, default=str)
        
        return {"messages": "Correlation analysis completed successfully", "correlation_analysis": correlation_results}
    except Exception as e:
        return {"error": f"Error in correlation analysis: {str(e)}"}


@tool
def outlier_detection(file_path: str, column_name: str, method: str = "iqr", task_folder: str = "") -> dict:
    """
    检测异常值
    :param file_path: 数据文件路径
    :param column_name: 要检测的列名
    :param method: 检测方法 ("iqr", "zscore", "both")
    :param task_folder: 任务文件夹路径
    :return: 异常值检测结果
    """
    try:
        # 读取数据
        df = pd.read_csv(file_path, encoding='utf-8')
        
        if column_name not in df.columns:
            return {"error": f"Column '{column_name}' not found in data"}
        
        data = df[column_name].dropna()
        outliers_info = {}
        
        # IQR方法
        if method in ["iqr", "both"]:
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            iqr_outliers = data[(data < lower_bound) | (data > upper_bound)]
            outliers_info["iqr_method"] = {
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
                "outliers_count": len(iqr_outliers),
                "outliers_percentage": (len(iqr_outliers) / len(data)) * 100,
                "outlier_values": iqr_outliers.tolist()
            }
        
        # Z-Score方法
        if method in ["zscore", "both"]:
            z_scores = np.abs((data - data.mean()) / data.std())
            zscore_outliers = data[z_scores > 3]
            outliers_info["zscore_method"] = {
                "threshold": 3,
                "outliers_count": len(zscore_outliers),
                "outliers_percentage": (len(zscore_outliers) / len(data)) * 100,
                "outlier_values": zscore_outliers.tolist()
            }
        
        # 综合分析
        analysis_summary = {
            "column_analyzed": column_name,
            "total_values": len(data),
            "data_statistics": {
                "mean": data.mean(),
                "median": data.median(),
                "std": data.std(),
                "min": data.min(),
                "max": data.max()
            },
            "outlier_detection_results": outliers_info
        }
        
        # 保存异常值检测结果
        if task_folder:
            outlier_file_path = os.path.join(task_folder, f"outlier_detection_{column_name}.json")
            full_outlier_path = os.path.join(os.getcwd(), outlier_file_path)
            with open(full_outlier_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_summary, f, ensure_ascii=False, indent=2, default=str)
        
        return {"messages": f"Outlier detection completed for column '{column_name}'", "outlier_analysis": analysis_summary}
    except Exception as e:
        return {"error": f"Error in outlier detection: {str(e)}"}


@tool
def data_export(data_dict: dict, file_name: str, export_format: str = "json", task_folder: str = "") -> dict:
    """
    导出数据到不同格式
    :param data_dict: 要导出的数据字典
    :param file_name: 文件名（不含扩展名）
    :param export_format: 导出格式 ("json", "csv", "txt")
    :param task_folder: 任务文件夹路径
    :return: 导出结果
    """
    try:
        # 确定文件路径
        if task_folder:
            base_path = os.path.join(task_folder, file_name)
            full_base_path = os.path.join(os.getcwd(), base_path)
        else:
            base_path = os.path.join("output", file_name)
            full_base_path = os.path.join(os.getcwd(), base_path)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(full_base_path), exist_ok=True)
        
        if export_format == "json":
            file_path = f"{full_base_path}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, ensure_ascii=False, indent=2, default=str)
                
        elif export_format == "csv":
            file_path = f"{full_base_path}.csv"
            # 如果数据是DataFrame格式
            if isinstance(data_dict, dict) and 'data' in data_dict:
                df = pd.DataFrame(data_dict['data'])
                df.to_csv(file_path, index=False, encoding='utf-8')
            else:
                # 尝试将字典转换为DataFrame
                df = pd.DataFrame([data_dict])
                df.to_csv(file_path, index=False, encoding='utf-8')
                
        elif export_format == "txt":
            file_path = f"{full_base_path}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                if isinstance(data_dict, dict):
                    for key, value in data_dict.items():
                        f.write(f"{key}: {value}\n")
                else:
                    f.write(str(data_dict))
        else:
            return {"error": f"Unsupported export format: {export_format}"}
        
        return {"messages": f"Data exported successfully to {file_path}", "export_path": file_path}
    except Exception as e:
        return {"error": f"Error exporting data: {str(e)}"}


@tool
def read_file_content(file_path: str, encoding: str = 'utf-8') -> dict:
    """
    读取文件内容
    :param file_path: 文件路径
    :param encoding: 文件编码
    :return: 文件内容
    """
    try:
        full_path = os.path.join(os.getcwd(), file_path)
        with open(full_path, 'r', encoding=encoding) as f:
            content = f.read()
        
        return {"messages": f"Successfully read file {file_path}", "content": content}
    except Exception as e:
        return {"error": f"Error reading file: {str(e)}"}


@tool
def list_files(directory_path: str = "output") -> dict:
    """
    列出目录中的文件
    :param directory_path: 目录路径
    :return: 文件列表
    """
    try:
        full_path = os.path.join(os.getcwd(), directory_path)
        
        if not os.path.exists(full_path):
            return {"error": f"Directory {directory_path} does not exist"}
        
        files = []
        for item in os.listdir(full_path):
            item_path = os.path.join(full_path, item)
            if os.path.isfile(item_path):
                file_info = {
                    "name": item,
                    "size": os.path.getsize(item_path),
                    "modified": datetime.fromtimestamp(os.path.getmtime(item_path)).strftime('%Y-%m-%d %H:%M:%S')
                }
                files.append(file_info)
            elif os.path.isdir(item_path):
                files.append({"name": item, "type": "directory"})
        
        return {"messages": f"Found {len(files)} items in {directory_path}", "files": files}
    except Exception as e:
        return {"error": f"Error listing files: {str(e)}"}


