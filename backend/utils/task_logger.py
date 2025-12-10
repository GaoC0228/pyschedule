"""
任务执行日志管理工具
将任务执行日志存储到文件系统而非数据库
"""
import os
from datetime import datetime
from pathlib import Path


class TaskLogger:
    """任务日志管理器"""
    
    def __init__(self, base_dir: str = "../logs/tasks"):
        """
        初始化任务日志管理器
        
        Args:
            base_dir: 日志基础目录（相对于backend目录）
        """
        # 获取项目根目录（backend的上一级）
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # 日志目录在项目根目录的logs/tasks下
        self.base_dir = os.path.join(current_dir, "..", "logs", "tasks")
        self.base_dir = os.path.abspath(self.base_dir)
        os.makedirs(self.base_dir, exist_ok=True)
    
    def get_log_file_path(self, task_id: int, execution_id: int) -> str:
        """
        获取任务执行日志文件路径
        
        Args:
            task_id: 任务ID
            execution_id: 执行记录ID
            
        Returns:
            日志文件完整路径
        """
        # 按任务ID分目录存储
        task_dir = os.path.join(self.base_dir, str(task_id))
        os.makedirs(task_dir, exist_ok=True)
        
        # 日志文件名格式：execution_{执行ID}_{时间戳}.log
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"execution_{execution_id}_{timestamp}.log"
        
        return os.path.join(task_dir, log_filename)
    
    def write_log(self, log_file: str, content: str, mode: str = 'a'):
        """
        写入日志内容
        
        Args:
            log_file: 日志文件路径
            content: 日志内容
            mode: 写入模式，'a'追加，'w'覆盖
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            with open(log_file, mode, encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            print(f"写入日志失败: {str(e)}")
    
    def read_log(self, log_file: str) -> str:
        """
        读取日志内容
        
        Args:
            log_file: 日志文件路径
            
        Returns:
            日志内容，如果文件不存在返回空字符串
        """
        if not os.path.exists(log_file):
            return ""
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"读取日志失败: {str(e)}"
    
    def delete_log(self, log_file: str):
        """
        删除日志文件
        
        Args:
            log_file: 日志文件路径
        """
        if os.path.exists(log_file):
            try:
                os.remove(log_file)
            except Exception as e:
                print(f"删除日志失败: {str(e)}")
    
    def list_task_logs(self, task_id: int):
        """
        列出任务的所有日志文件
        
        Args:
            task_id: 任务ID
            
        Returns:
            日志文件列表
        """
        task_dir = os.path.join(self.base_dir, str(task_id))
        if not os.path.exists(task_dir):
            return []
        
        log_files = []
        for filename in os.listdir(task_dir):
            if filename.endswith('.log'):
                filepath = os.path.join(task_dir, filename)
                log_files.append({
                    'filename': filename,
                    'path': filepath,
                    'size': os.path.getsize(filepath),
                    'modified_time': datetime.fromtimestamp(os.path.getmtime(filepath))
                })
        
        # 按修改时间倒序排列
        log_files.sort(key=lambda x: x['modified_time'], reverse=True)
        return log_files


# 全局实例
task_logger = TaskLogger()
