#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
路径管理模块 - 统一管理所有数据目录路径
为Docker容器化提供灵活的持久化目录配置
"""

import os
from pathlib import Path

# 项目根目录（backend的父目录）
# 通过环境变量可以覆盖，便于Docker挂载
PROJECT_ROOT = os.getenv('PROJECT_ROOT', str(Path(__file__).parent.parent.parent))

# 数据根目录（可通过环境变量配置，用于Docker持久化）
DATA_ROOT = os.getenv('DATA_ROOT', os.path.join(PROJECT_ROOT, 'data'))

# 日志根目录（可通过环境变量配置，用于Docker持久化）
LOGS_ROOT = os.getenv('LOGS_ROOT', os.path.join(PROJECT_ROOT, 'logs'))

# 上传文件目录
UPLOADS_DIR = os.path.join(PROJECT_ROOT, 'backend', 'uploads')


def get_task_data_dir(task_id: int) -> str:
    """
    获取任务数据目录
    
    Args:
        task_id: 任务ID
        
    Returns:
        任务数据目录路径
    """
    return os.path.join(DATA_ROOT, 'tasks', str(task_id))


def get_task_input_dir(task_id: int) -> str:
    """
    获取任务输入文件目录
    
    Args:
        task_id: 任务ID
        
    Returns:
        任务输入目录路径
    """
    return os.path.join(get_task_data_dir(task_id), 'inputs')


def get_execution_output_dir(task_id: int, execution_id: int) -> str:
    """
    获取任务执行输出目录
    
    Args:
        task_id: 任务ID
        execution_id: 执行ID
        
    Returns:
        执行输出目录路径
    """
    return os.path.join(get_task_data_dir(task_id), 'executions', str(execution_id))


def get_execution_output_file(task_id: int, execution_id: int, filename: str) -> str:
    """
    获取任务执行产出文件的完整路径
    
    Args:
        task_id: 任务ID
        execution_id: 执行ID
        filename: 文件名
        
    Returns:
        文件完整路径
    """
    return os.path.join(get_execution_output_dir(task_id, execution_id), filename)


def get_task_log_dir(task_id: int) -> str:
    """
    获取任务日志目录
    
    Args:
        task_id: 任务ID
        
    Returns:
        任务日志目录路径
    """
    return os.path.join(LOGS_ROOT, 'tasks', str(task_id))


def get_execution_log_file(task_id: int, execution_id: int, timestamp: str) -> str:
    """
    获取执行日志文件路径
    
    Args:
        task_id: 任务ID
        execution_id: 执行ID
        timestamp: 时间戳字符串
        
    Returns:
        日志文件路径
    """
    return os.path.join(
        get_task_log_dir(task_id),
        f'execution_{execution_id}_{timestamp}.log'
    )


def ensure_dir(directory: str) -> str:
    """
    确保目录存在，不存在则创建
    
    Args:
        directory: 目录路径
        
    Returns:
        目录路径
    """
    os.makedirs(directory, exist_ok=True)
    return directory


# 初始化必要的目录
def init_directories():
    """初始化所有必要的数据目录"""
    ensure_dir(DATA_ROOT)
    ensure_dir(LOGS_ROOT)
    ensure_dir(UPLOADS_DIR)
    ensure_dir(os.path.join(DATA_ROOT, 'tasks'))
    ensure_dir(os.path.join(LOGS_ROOT, 'tasks'))


# 模块导入时自动初始化目录
init_directories()


# 导出配置信息（用于调试和日志）
def get_config_info() -> dict:
    """获取当前路径配置信息"""
    return {
        'PROJECT_ROOT': PROJECT_ROOT,
        'DATA_ROOT': DATA_ROOT,
        'LOGS_ROOT': LOGS_ROOT,
        'UPLOADS_DIR': UPLOADS_DIR,
    }


if __name__ == '__main__':
    # 测试模块
    import json
    print("路径配置信息:")
    print(json.dumps(get_config_info(), indent=2, ensure_ascii=False))
    print("\n示例路径:")
    print(f"任务数据目录 (ID=1): {get_task_data_dir(1)}")
    print(f"任务输入目录 (ID=1): {get_task_input_dir(1)}")
    print(f"执行输出目录 (ID=1, EX=10): {get_execution_output_dir(1, 10)}")
    print(f"执行输出文件 (ID=1, EX=10): {get_execution_output_file(1, 10, 'report.csv')}")
