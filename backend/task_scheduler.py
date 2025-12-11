import os
import sys
import subprocess
import json
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Task, TaskExecution, TaskStatus
from utils.task_logger import task_logger
from utils.paths import (
    get_task_data_dir, get_task_input_dir, get_execution_output_dir,
    get_task_log_dir, get_execution_log_file, ensure_dir
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        logger.info("任务调度器已启动")
    
    def add_task(self, task_id: int, cron_expression: str):
        """添加定时任务，返回下次执行时间"""
        try:
            job_id = f"task_{task_id}"
            # 移除已存在的任务
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            
            # 添加新任务
            job = self.scheduler.add_job(
                func=self.execute_task,
                trigger=CronTrigger.from_crontab(cron_expression),
                id=job_id,
                args=[task_id],
                replace_existing=True
            )
            logger.info(f"任务 {task_id} 已添加到调度器，下次执行: {job.next_run_time}")
            
            # 返回下次执行时间
            return job.next_run_time
        except Exception as e:
            logger.error(f"添加任务 {task_id} 失败: {str(e)}")
            raise
    
    def remove_task(self, task_id: int):
        """移除定时任务"""
        try:
            job_id = f"task_{task_id}"
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                logger.info(f"任务 {task_id} 已从调度器移除")
        except Exception as e:
            logger.error(f"移除任务 {task_id} 失败: {str(e)}")
    
    def execute_task(self, task_id: int, executed_by: int = None, trigger_type: str = "scheduled"):
        """执行任务
        
        Args:
            task_id: 任务ID
            executed_by: 执行用户ID（手动执行时传入）
            trigger_type: 触发方式 scheduled/manual
        """
        db = SessionLocal()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task or not task.is_active:
                logger.warning(f"任务 {task_id} 不存在或已禁用")
                return
            
            # 创建执行记录
            execution = TaskExecution(
                task_id=task_id,
                executed_by=executed_by,
                trigger_type=trigger_type,
                status=TaskStatus.RUNNING,
                start_time=datetime.now()  # 使用本地时间
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)
            
            # 创建日志文件
            log_file = task_logger.get_log_file_path(task_id, execution.id)
            execution.log_file = log_file
            
            # 更新任务状态
            task.status = TaskStatus.RUNNING
            task.last_run_at = datetime.now()  # 使用本地时间
            db.commit()
            
            logger.info(f"开始执行任务 {task_id}: {task.name}")
            
            # 使用统一的路径工具创建任务数据目录
            task_data_dir = ensure_dir(get_task_data_dir(task_id))
            input_dir = ensure_dir(get_task_input_dir(task_id))
            output_dir = ensure_dir(get_execution_output_dir(task_id, execution.id))
            
            logger.info(f"任务输出目录: {output_dir}")
            
            # 写入日志头部
            log_header = f"""
{'='*80}
任务执行日志
{'='*80}
任务ID: {task_id}
任务名称: {task.name}
执行ID: {execution.id}
触发方式: {trigger_type}
开始时间: {execution.start_time.strftime('%Y-%m-%d %H:%M:%S')}
执行脚本: {task.script_path}
输出目录: {output_dir}
{'='*80}

"""
            task_logger.write_log(log_file, log_header, mode='w')
            
            # 设置环境变量
            env = os.environ.copy()
            
            # 添加PYTHONPATH，让脚本可以导入backend的模块（如db_configs）
            # __file__ 是 /app/task_scheduler.py，dirname一次得到 /app
            backend_path = os.path.dirname(os.path.abspath(__file__))  # /app
            current_pythonpath = env.get('PYTHONPATH', '')
            if current_pythonpath:
                env['PYTHONPATH'] = f"{backend_path}:{current_pythonpath}"
            else:
                env['PYTHONPATH'] = backend_path
            
            env.update({
                'TASK_ID': str(task_id),
                'TASK_NAME': task.name,
                'EXECUTION_ID': str(execution.id),
                'TASK_DIR': task_data_dir,
                'INPUT_DIR': input_dir,
                'OUTPUT_DIR': output_dir,
                'EXEC_DATE': execution.start_time.strftime('%Y%m%d'),
                'EXEC_TIME': execution.start_time.strftime('%H%M%S'),
                'EXEC_DATETIME': execution.start_time.strftime('%Y%m%d_%H%M%S'),
            })
            
            # 执行Python脚本
            try:
                # 确保脚本路径是绝对路径（因为我们改变了工作目录）
                script_absolute_path = os.path.abspath(task.script_path)
                
                # 构建命令：python script.py [参数]
                command = [sys.executable, script_absolute_path]
                
                # 添加命令行参数（如果有）
                if task.script_params:
                    # 使用shlex解析参数，支持引号和转义
                    import shlex
                    params = shlex.split(task.script_params)
                    command.extend(params)
                    logger.info(f"执行命令: {' '.join(command)}")
                
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=3600,  # 1小时超时
                    env=env,  # 传入环境变量
                    cwd=output_dir  # ⭐ 设置工作目录为输出目录，脚本可以直接在当前目录创建文件
                )
                
                execution.end_time = datetime.now()  # 使用本地时间
                execution.exit_code = result.returncode
                
                # 写入执行输出
                if result.stdout:
                    task_logger.write_log(log_file, "\n标准输出:\n" + "="*80 + "\n")
                    task_logger.write_log(log_file, result.stdout)
                
                # 写入错误输出
                if result.stderr:
                    task_logger.write_log(log_file, "\n\n错误输出:\n" + "="*80 + "\n")
                    task_logger.write_log(log_file, result.stderr)
                
                # 写入日志尾部
                log_footer = f"""
\n{'='*80}
执行结束
{'='*80}
结束时间: {execution.end_time.strftime('%Y-%m-%d %H:%M:%S')}
执行时长: {(execution.end_time - execution.start_time).total_seconds():.2f}秒
退出码: {result.returncode}
状态: {'成功' if result.returncode == 0 else '失败'}
{'='*80}
"""
                task_logger.write_log(log_file, log_footer)
                
                # 扫描产出文件
                output_files = self._scan_output_files(output_dir)
                if output_files:
                    execution.output_files = json.dumps(output_files, ensure_ascii=False)
                    logger.info(f"任务 {task_id} 产出了 {len(output_files)} 个文件")
                
                if result.returncode == 0:
                    execution.status = TaskStatus.SUCCESS
                    task.status = TaskStatus.SUCCESS
                    logger.info(f"任务 {task_id} 执行成功")
                else:
                    execution.status = TaskStatus.FAILED
                    task.status = TaskStatus.FAILED
                    logger.error(f"任务 {task_id} 执行失败，退出码: {result.returncode}")
                
            except subprocess.TimeoutExpired:
                execution.end_time = datetime.now()  # 使用本地时间
                execution.status = TaskStatus.FAILED
                execution.exit_code = -1
                task.status = TaskStatus.FAILED
                
                error_msg = f"\n\n任务执行超时（超过3600秒）\n结束时间: {execution.end_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                task_logger.write_log(log_file, error_msg)
                logger.error(f"任务 {task_id} 执行超时")
            
            except Exception as e:
                execution.end_time = datetime.now()  # 使用本地时间
                execution.status = TaskStatus.FAILED
                execution.exit_code = -1
                task.status = TaskStatus.FAILED
                
                error_msg = f"\n\n执行异常:\n{str(e)}\n结束时间: {execution.end_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                task_logger.write_log(log_file, error_msg)
                logger.error(f"任务 {task_id} 执行异常: {str(e)}")
            
            db.commit()
            
        except Exception as e:
            logger.error(f"执行任务 {task_id} 时发生错误: {str(e)}")
            db.rollback()
        finally:
            db.close()
    
    def _scan_output_files(self, output_dir: str) -> list:
        """扫描输出目录中的文件
        
        Args:
            output_dir: 输出目录路径
            
        Returns:
            文件信息列表
        """
        files = []
        try:
            if not os.path.exists(output_dir):
                return files
            
            for filename in os.listdir(output_dir):
                filepath = os.path.join(output_dir, filename)
                if os.path.isfile(filepath):
                    file_stat = os.stat(filepath)
                    files.append({
                        'name': filename,
                        'path': filepath,
                        'size': file_stat.st_size,
                        'created_at': datetime.fromtimestamp(file_stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            return files
        except Exception as e:
            logger.error(f"扫描输出文件失败: {str(e)}")
            return files
    
    def load_tasks_from_db(self):
        """从数据库加载所有活跃任务"""
        db = SessionLocal()
        try:
            tasks = db.query(Task).filter(Task.is_active == True).all()
            for task in tasks:
                try:
                    self.add_task(task.id, task.cron_expression)
                except Exception as e:
                    logger.error(f"加载任务 {task.id} 失败: {str(e)}")
            logger.info(f"已加载 {len(tasks)} 个活跃任务")
        finally:
            db.close()
    
    def shutdown(self):
        """关闭调度器"""
        self.scheduler.shutdown()
        logger.info("任务调度器已关闭")


# 全局调度器实例
task_scheduler = TaskScheduler()
