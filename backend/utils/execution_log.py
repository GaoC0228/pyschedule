#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
脚本执行日志管理
将执行日志保存到文件系统，避免数据库过大
"""

import os
from datetime import datetime
from typing import Optional

# 执行日志根目录
# __file__ = /app/utils/execution_log.py
# dirname 2次得到 /app，再拼接 logs/execution
EXECUTION_LOG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),  # /app
    "logs",
    "execution"
)

# 确保目录存在
os.makedirs(EXECUTION_LOG_DIR, exist_ok=True)


def generate_log_filename(audit_log_id: int, script_name: str, trigger_type: str) -> str:
    """
    生成日志文件名
    格式: {audit_log_id}_{trigger_type}_{script_name}_{timestamp}.log
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # 清理脚本名中的特殊字符
    safe_script_name = script_name.replace('/', '_').replace('\\', '_')
    filename = f"{audit_log_id}_{trigger_type}_{safe_script_name}_{timestamp}.log"
    return filename


def save_execution_log(audit_log_id: int, script_name: str, trigger_type: str, content: str) -> str:
    """
    保存执行日志到文件
    
    Args:
        audit_log_id: 审计日志ID
        script_name: 脚本名称
        trigger_type: 触发类型 (manual/interactive)
        content: 日志内容
        
    Returns:
        相对路径
    """
    filename = generate_log_filename(audit_log_id, script_name, trigger_type)
    filepath = os.path.join(EXECUTION_LOG_DIR, filename)
    
    # 写入文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 返回相对路径
    return f"logs/execution/{filename}"


def read_execution_log(relative_path: str) -> Optional[str]:
    """
    读取执行日志
    
    Args:
        relative_path: 相对路径，如 logs/execution/xxx.log
        
    Returns:
        日志内容，如果文件不存在返回None
    """
    # 构建完整路径
    # __file__ = /app/utils/execution_log.py, dirname 2次得到 /app
    base_dir = os.path.dirname(os.path.dirname(__file__))
    filepath = os.path.join(base_dir, relative_path)
    
    if not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None


def delete_execution_log(relative_path: str) -> bool:
    """
    删除执行日志文件
    
    Args:
        relative_path: 相对路径
        
    Returns:
        是否成功删除
    """
    # __file__ = /app/utils/execution_log.py, dirname 2次得到 /app
    base_dir = os.path.dirname(os.path.dirname(__file__))
    filepath = os.path.join(base_dir, relative_path)
    
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            return True
        except Exception:
            return False
    return False
