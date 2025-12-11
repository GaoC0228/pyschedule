"""
脚本执行WebSocket - 实时日志流
支持实时输出和终止功能
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user_ws
from models import User
import asyncio
import subprocess
import os
import logging
from datetime import datetime
from typing import Dict
import threading
import signal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

# 全局执行管理器：{execution_id: {process, websocket, status}}
RUNNING_EXECUTIONS: Dict[str, dict] = {}


class ScriptExecutor:
    """脚本执行器 - 支持实时输出和终止"""
    
    def __init__(self, execution_id: str, full_path: str, websocket: WebSocket):
        self.execution_id = execution_id
        self.full_path = full_path
        self.websocket = websocket
        self.process = None
        self.should_stop = False
        
    async def send_log(self, message: str, log_type: str = "info"):
        """发送日志到前端"""
        try:
            await self.websocket.send_json({
                "type": "log",
                "log_type": log_type,
                "message": message,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"发送日志失败: {e}")
    
    async def execute(self):
        """执行脚本并实时输出"""
        try:
            await self.send_log(f"开始执行脚本: {os.path.basename(self.full_path)}", "info")
            
            # 设置环境变量
            env = os.environ.copy()
            env['PYTHONPATH'] = f"/app:{env.get('PYTHONPATH', '')}"
            env['PYTHONUNBUFFERED'] = '1'  # 禁用输出缓冲
            
            # 启动进程
            self.process = subprocess.Popen(
                ["python", "-u", self.full_path],  # -u 强制unbuffered
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(self.full_path),
                env=env,
                text=True,
                bufsize=1  # 行缓冲
            )
            
            # 保存进程信息
            RUNNING_EXECUTIONS[self.execution_id] = {
                "process": self.process,
                "websocket": self.websocket,
                "status": "running",
                "start_time": datetime.now()
            }
            
            # 创建任务同时读取stdout和stderr
            tasks = [
                asyncio.create_task(self._read_stream(self.process.stdout, "stdout")),
                asyncio.create_task(self._read_stream(self.process.stderr, "stderr"))
            ]
            
            # 等待进程完成或被终止
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # 等待进程结束
            returncode = self.process.poll()
            if returncode is None:
                # 如果进程还在运行，等待它
                await asyncio.get_event_loop().run_in_executor(None, self.process.wait)
                returncode = self.process.returncode
            
            # 发送完成消息
            if self.should_stop:
                await self.send_log("脚本已被用户终止", "warning")
                await self.websocket.send_json({
                    "type": "complete",
                    "returncode": returncode or -1,
                    "success": False,
                    "message": "已终止"
                })
            else:
                success = returncode == 0
                await self.send_log(
                    f"脚本执行{'成功' if success else '失败'} (退出码: {returncode})",
                    "success" if success else "error"
                )
                await self.websocket.send_json({
                    "type": "complete",
                    "returncode": returncode,
                    "success": success,
                    "message": "执行完成"
                })
                
        except Exception as e:
            logger.error(f"脚本执行异常: {e}", exc_info=True)
            await self.send_log(f"执行异常: {str(e)}", "error")
            await self.websocket.send_json({
                "type": "complete",
                "returncode": -1,
                "success": False,
                "message": f"异常: {str(e)}"
            })
        finally:
            # 清理
            if self.execution_id in RUNNING_EXECUTIONS:
                del RUNNING_EXECUTIONS[self.execution_id]
    
    async def _read_stream(self, stream, stream_name: str):
        """读取输出流并实时发送"""
        loop = asyncio.get_event_loop()
        try:
            while True:
                if self.should_stop:
                    break
                    
                # 在线程池中读取一行（避免阻塞）
                line = await loop.run_in_executor(None, stream.readline)
                
                if not line:
                    break
                
                line = line.rstrip('\n\r')
                if line:
                    log_type = "error" if stream_name == "stderr" else "info"
                    await self.send_log(line, log_type)
                    
        except Exception as e:
            logger.error(f"读取{stream_name}失败: {e}")
    
    def stop(self):
        """终止脚本执行"""
        self.should_stop = True
        if self.process and self.process.poll() is None:
            try:
                # 尝试优雅终止
                self.process.terminate()
                # 等待3秒
                try:
                    self.process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    # 强制杀死
                    self.process.kill()
                logger.info(f"进程已终止: {self.execution_id}")
            except Exception as e:
                logger.error(f"终止进程失败: {e}")


@router.websocket("/ws/script-execution/{execution_id}")
async def script_execution_websocket(
    websocket: WebSocket,
    execution_id: str,
    db: Session = Depends(get_db)
):
    """脚本执行WebSocket - 实时日志流"""
    await websocket.accept()
    
    # 验证用户
    current_user = await get_current_user_ws(websocket, db)
    if not current_user:
        await websocket.send_json({'type': 'error', 'message': '未授权'})
        await websocket.close()
        return
    
    logger.info(f"用户 {current_user.username} 建立脚本执行WebSocket: {execution_id}")
    
    try:
        # 等待接收执行参数
        data = await websocket.receive_json()
        
        if data.get('type') == 'start':
            file_path = data.get('file_path')
            
            if not file_path:
                await websocket.send_json({'type': 'error', 'message': '缺少file_path参数'})
                return
            
            # 权限检查
            from routers.workspace import check_path_permission
            try:
                full_path = check_path_permission(current_user, file_path, require_write=False)
            except Exception as e:
                await websocket.send_json({'type': 'error', 'message': str(e)})
                return
            
            if not os.path.exists(full_path):
                await websocket.send_json({'type': 'error', 'message': '文件不存在'})
                return
            
            if not full_path.endswith('.py'):
                await websocket.send_json({'type': 'error', 'message': '只能执行Python脚本'})
                return
            
            # 创建执行器并执行
            executor = ScriptExecutor(execution_id, full_path, websocket)
            
            # 监听终止命令
            async def listen_for_stop():
                try:
                    while True:
                        msg = await websocket.receive_json()
                        if msg.get('type') == 'stop':
                            logger.info(f"收到终止命令: {execution_id}")
                            executor.stop()
                            break
                except WebSocketDisconnect:
                    logger.info(f"WebSocket断开: {execution_id}")
                    executor.stop()
                except Exception as e:
                    logger.error(f"监听终止命令异常: {e}")
            
            # 同时运行执行和监听
            await asyncio.gather(
                executor.execute(),
                listen_for_stop(),
                return_exceptions=True
            )
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket连接断开: {execution_id}")
        # 如果WebSocket断开，终止执行
        if execution_id in RUNNING_EXECUTIONS:
            exec_info = RUNNING_EXECUTIONS[execution_id]
            process = exec_info.get('process')
            if process and process.poll() is None:
                process.terminate()
    except Exception as e:
        logger.error(f"WebSocket异常: {e}", exc_info=True)
    finally:
        # 清理
        if execution_id in RUNNING_EXECUTIONS:
            del RUNNING_EXECUTIONS[execution_id]
        logger.info(f"脚本执行WebSocket关闭: {execution_id}")


@router.post("/script-execution/stop/{execution_id}")
async def stop_script_execution(
    execution_id: str,
    db: Session = Depends(get_db)
):
    """终止正在执行的脚本（REST API方式）"""
    if execution_id not in RUNNING_EXECUTIONS:
        return {"success": False, "message": "执行不存在或已完成"}
    
    exec_info = RUNNING_EXECUTIONS[execution_id]
    process = exec_info.get('process')
    
    if process and process.poll() is None:
        try:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
            
            return {"success": True, "message": "脚本已终止"}
        except Exception as e:
            logger.error(f"终止脚本失败: {e}")
            return {"success": False, "message": f"终止失败: {str(e)}"}
    
    return {"success": False, "message": "进程已结束"}
