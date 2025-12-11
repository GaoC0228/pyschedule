#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WebSocket终端路由
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
import json
import asyncio
import os
import logging
from datetime import datetime
from database import get_db
from models import User
from auth import get_current_user_ws
from terminal import TerminalManager
from audit import create_audit_log, AuditAction, ResourceType
from utils.execution_log import save_execution_log


def get_websocket_client_ip(websocket: WebSocket) -> str:
    """从WebSocket获取客户端真实IP"""
    # 优先从X-Real-IP获取
    real_ip = websocket.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    
    # 从X-Forwarded-For获取
    forwarded_for = websocket.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    # 降级使用直接连接IP
    if websocket.client:
        return websocket.client.host
    
    return "unknown"

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

# 工作区目录
WORKSPACE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "work")

# 全局终端管理器
terminal_manager = TerminalManager(WORKSPACE_DIR)

# 交互式会话缓存: { session_id: { audit_log_id, transcript, start_time, script_path } }
SESSION_DATA = {}


@router.websocket("/ws/terminal/{session_id}")
async def terminal_websocket(
    websocket: WebSocket,
    session_id: str,
    db: Session = Depends(get_db)
):
    """WebSocket终端连接"""
    await websocket.accept()
    try:
        # 用户认证
        current_user = await get_current_user_ws(websocket, db)
        
        if not current_user:
            logger.warning(f"未授权的WebSocket连接尝试: session={session_id}")
            try:
                await websocket.send_json({
                    'type': 'error',
                    'message': 'Token无效或已过期，请重新登录'
                })
            except:
                pass
            await websocket.close(code=1008)
            return
        
        logger.info(f"WebSocket连接建立: session={session_id}, user={current_user.username}")
        
        # 等待客户端发送启动命令
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                message = json.loads(data)
                
                msg_type = message.get('type')
                
                if msg_type == 'start':
                    # 启动终端
                    script_path = message.get('script_path')
                    cols = message.get('cols', 80)
                    rows = message.get('rows', 24)
                    # 获取执行模式：auto（自动执行并关闭）或 interactive（交互式）
                    execution_mode = message.get('execution_mode', 'interactive')
                    
                    logger.info(f"启动终端: script={script_path}, user={current_user.username}")
                    
                    try:
                        terminal = terminal_manager.create_terminal(session_id, script_path, cols, rows)
                        
                        # 创建审计日志（仅一次，防止重复）
                        if session_id not in SESSION_DATA:
                            # 先检查是否已有同一用户同一脚本的running记录
                            from models import AuditLog
                            existing_log = db.query(AuditLog).filter(
                                AuditLog.user_id == current_user.id,
                                AuditLog.script_path == script_path,
                                AuditLog.status == "running",
                                AuditLog.action == AuditAction.WORKSPACE_EXECUTE
                            ).order_by(AuditLog.id.desc()).first()
                            
                            if existing_log:
                                # 复用现有记录
                                logger.info(f"复用现有审计记录: {existing_log.id}")
                                audit_log = existing_log
                            else:
                                # 创建新记录
                                # 根据execution_mode设置trigger_type
                                trigger_type = "interactive" if execution_mode == "interactive" else "manual"
                                
                                audit_log = create_audit_log(
                                    db=db,
                                    user=current_user,
                                    action=AuditAction.WORKSPACE_EXECUTE,
                                    resource_type=ResourceType.SCRIPT,
                                    script_name=os.path.basename(script_path) if script_path else None,
                                    script_path=script_path,
                                    status="running",
                                    details={
                                        "file_path": script_path,
                                        "trigger_type": trigger_type,
                                        "execution_mode": execution_mode,
                                        "session_id": session_id,
                                        "log_file": ""
                                    },
                                    ip_address=get_websocket_client_ip(websocket)
                                )
                            
                            SESSION_DATA[session_id] = {
                                'audit_log_id': audit_log.id,
                                'transcript': [],
                                'start_time': datetime.now(),
                                'script_path': script_path or '',
                                'execution_mode': execution_mode
                            }
                        
                        await websocket.send_json({
                            'type': 'started',
                            'message': '终端已启动'
                        })
                        break
                    except Exception as e:
                        await websocket.send_json({
                            'type': 'error',
                            'message': f'启动失败: {str(e)}'
                        })
                        return
                        
            except asyncio.TimeoutError:
                continue
            except WebSocketDisconnect:
                logger.info(f"WebSocket连接断开: session={session_id}")
                return
        
        # 主循环：处理输入输出
        while terminal and terminal.is_alive():
            try:
                # 读取终端输出
                output = terminal.read(timeout=0.05)
                if output:
                    output_str = output.decode('utf-8', errors='replace')
                    # 记录到transcript
                    if session_id in SESSION_DATA:
                        SESSION_DATA[session_id]['transcript'].append(output_str)
                    await websocket.send_json({
                        'type': 'output',
                        'data': output_str
                    })
                
                # 接收用户输入
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=0.05)
                    message = json.loads(data)
                    
                    msg_type = message.get('type')
                    
                    if msg_type == 'input':
                        # 用户输入
                        input_data = message.get('data', '')
                        terminal.write(input_data)
                    
                    elif msg_type == 'resize':
                        # 调整终端大小
                        cols = message.get('cols', 80)
                        rows = message.get('rows', 24)
                        terminal.resize(cols, rows)
                    
                    elif msg_type == 'close':
                        # 关闭终端
                        break
                        
                except asyncio.TimeoutError:
                    continue
                    
            except WebSocketDisconnect:
                logger.info(f"WebSocket连接断开: session={session_id}")
                break
            except Exception as e:
                logger.error(f"终端循环错误: {str(e)}")
                break
        
        # 发送进程结束消息
        if terminal and not terminal.is_alive():
            returncode = terminal.get_exit_status()
            await websocket.send_json({
                'type': 'exit',
                'message': '进程已结束',
                'returncode': returncode
            })
        
    except Exception as e:
        logger.error(f"WebSocket错误: {str(e)}")
        try:
            await websocket.send_json({
                'type': 'error',
                'message': str(e)
            })
        except:
            pass
    
    finally:
        # 保存交互式日志并更新审计记录
        try:
            session_data = SESSION_DATA.get(session_id)
            if session_data:
                # 合并所有输出
                transcript = ''.join(session_data['transcript'])
                
                # 保存到日志文件
                log_file_path = save_execution_log(
                    audit_log_id=session_data['audit_log_id'],
                    script_name=os.path.basename(session_data['script_path']) or 'interactive',
                    trigger_type="interactive",
                    content=transcript
                )
                
                # 更新审计日志
                from models import AuditLog
                audit_log = db.query(AuditLog).filter(AuditLog.id == session_data['audit_log_id']).first()
                if audit_log:
                    duration = (datetime.now() - session_data['start_time']).total_seconds()
                    audit_log.status = "success"  # 交互式执行默认成功
                    audit_log.execution_duration = duration
                    details = json.loads(audit_log.details) if audit_log.details else {}
                    details["log_file"] = log_file_path
                    audit_log.details = json.dumps(details, ensure_ascii=False)
                    db.commit()
                    logger.info(f"交互式日志已保存: {log_file_path}, audit_id={session_data['audit_log_id']}")
                else:
                    logger.warning(f"未找到审计记录: {session_data['audit_log_id']}")
            else:
                logger.warning(f"未找到SESSION_DATA: {session_id}, 可能是重复连接导致")
                # 尝试清理所有running状态的交互式记录（无log_file的）
                from models import AuditLog
                orphan_logs = db.query(AuditLog).filter(
                    AuditLog.status == "running",
                    AuditLog.details.like('%"trigger_type": "interactive"%')
                ).all()
                for log in orphan_logs:
                    details = json.loads(log.details) if log.details else {}
                    if not details.get("log_file"):
                        log.status = "failed"
                        log.execution_duration = 0
                        logger.info(f"清理孤儿审计记录: {log.id}")
                db.commit()
        except Exception as e:
            logger.error(f"保存交互式日志失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            db.rollback()
        finally:
            # 清理缓存
            if session_id in SESSION_DATA:
                SESSION_DATA.pop(session_id, None)
        
        # 清理终端
        if session_id:
            terminal_manager.close_terminal(session_id)
        
        # 关闭WebSocket
        try:
            await websocket.close()
        except:
            pass
        
        logger.info(f"WebSocket连接已关闭: session={session_id}")
