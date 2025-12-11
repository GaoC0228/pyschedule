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
    
    def write_log(self, log_file: str, content: str, mode: str = 'a', max_size_mb: int = 50):
        """
        写入日志内容（带大小限制）
        
        Args:
            log_file: 日志文件路径
            content: 日志内容
            mode: 写入模式，'a'追加，'w'覆盖
            max_size_mb: 最大文件大小（MB），超过则截断
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            # 检查文件大小，如果超过限制，添加警告并截断
            if mode == 'a' and os.path.exists(log_file):
                file_size = os.path.getsize(log_file)
                max_size_bytes = max_size_mb * 1024 * 1024
                
                if file_size > max_size_bytes:
                    # 添加截断警告
                    warning = f"\n\n{'='*80}\n⚠️ 日志文件已达到{max_size_mb}MB限制，停止记录新日志\n{'='*80}\n"
                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write(warning)
                    return  # 不再写入
            
            with open(log_file, mode, encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            print(f"写入日志失败: {str(e)}")
    
    def read_log(self, log_file: str, max_lines: int = 1000) -> str:
        """
        读取日志内容（优化版：只读取最后N行，避免大文件卡顿）
        
        Args:
            log_file: 日志文件路径
            max_lines: 最多读取的行数（从文件末尾开始）
            
        Returns:
            日志内容，如果文件不存在返回空字符串
        """
        if not os.path.exists(log_file):
            return ""
        
        try:
            # 检查文件大小
            file_size = os.path.getsize(log_file)
            
            # 如果文件很小（<1MB），直接读取全部
            if file_size < 1024 * 1024:  # 1MB
                with open(log_file, 'r', encoding='utf-8') as f:
                    return f.read()
            
            # 大文件：只读取最后N行
            lines = []
            with open(log_file, 'r', encoding='utf-8') as f:
                # 使用deque自动保持最后N行
                from collections import deque
                lines = deque(f, maxlen=max_lines)
            
            content = ''.join(lines)
            
            # 如果读取的是部分内容，添加提示
            if file_size > 1024 * 1024:
                size_mb = file_size / (1024 * 1024)
                header = f"⚠️ 日志文件较大({size_mb:.1f}MB)，仅显示最后{max_lines}行\n" + "="*80 + "\n\n"
                content = header + content
            
            return content
            
        except Exception as e:
            return f"读取日志失败: {str(e)}"
    
    def get_log_info(self, log_file: str) -> dict:
        """
        获取日志文件信息
        
        Args:
            log_file: 日志文件路径
            
        Returns:
            包含文件大小、行数等信息的字典
        """
        if not os.path.exists(log_file):
            return {"exists": False}
        
        try:
            file_size = os.path.getsize(log_file)
            size_mb = file_size / (1024 * 1024)
            
            # 快速统计行数（只对小文件）
            line_count = 0
            if file_size < 10 * 1024 * 1024:  # 小于10MB
                with open(log_file, 'r', encoding='utf-8') as f:
                    line_count = sum(1 for _ in f)
            
            return {
                "exists": True,
                "size_bytes": file_size,
                "size_mb": round(size_mb, 2),
                "line_count": line_count,
                "is_large": file_size > 1024 * 1024  # 超过1MB算大文件
            }
        except Exception as e:
            return {"exists": True, "error": str(e)}
    
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
