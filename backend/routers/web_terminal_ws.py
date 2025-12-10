#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Web终端WebSocket接口
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from models import User
from auth import get_current_user_ws
from utils.web_terminal import web_terminal_manager
import asyncio
import json
import logging
import uuid

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/api/ws/web-terminal")
async def web_terminal_websocket(
    websocket: WebSocket,
    token: str = Query(...),
    cols: int = Query(80),
    rows: int = Query(24),
    db: Session = Depends(get_db)
):
    """Web终端WebSocket连接"""
    await websocket.accept()
    
    terminal_id = None
    terminal = None
    current_user = None
    
    try:
        # 验证用户（仅管理员可访问）
        current_user = await get_current_user_ws(websocket, db)
        if not current_user:
            await websocket.send_json({
                'type': 'error',
                'message': '认证失败'
            })
            await websocket.close()
            return
        
        if current_user.role != "admin":
            await websocket.send_json({
                'type': 'error',
                'message': '需要管理员权限才能使用Web终端'
            })
            await websocket.close()
            return
        
        # 创建终端
        terminal_id = f"web_terminal_{current_user.id}_{uuid.uuid4().hex[:8]}"
        terminal = web_terminal_manager.create_terminal(
            terminal_id=terminal_id,
            user_id=current_user.id,
            cols=cols,
            rows=rows
        )
        
        # 发送启动成功消息
        await websocket.send_json({
            'type': 'started',
            'message': 'Web终端已启动',
            'terminal_id': terminal_id
        })
        
        # 创建读取任务
        async def read_terminal():
            """从终端读取数据并发送到WebSocket"""
            while terminal.is_alive():
                try:
                    data = terminal.read(timeout=0.05)
                    if data:
                        await websocket.send_text(data.decode('utf-8', errors='ignore'))
                    await asyncio.sleep(0.01)
                except Exception as e:
                    logger.error(f"读取终端数据失败: {e}")
                    break
        
        # 启动读取任务
        read_task = asyncio.create_task(read_terminal())
        
        # 处理客户端输入
        while True:
            message = await websocket.receive()
            
            if message['type'] == 'websocket.disconnect':
                break
            
            if message['type'] == 'websocket.receive':
                if 'text' in message:
                    data = message['text']
                    
                    # 尝试解析JSON（用于控制命令）
                    try:
                        cmd = json.loads(data)
                        if cmd.get('type') == 'resize':
                            terminal.resize(cmd.get('cols', 80), cmd.get('rows', 24))
                            continue
                        elif cmd.get('type') == 'input':
                            data = cmd.get('data', '')
                    except:
                        pass
                    
                    # 写入终端
                    if data:
                        terminal.write(data)
        
        # 取消读取任务
        read_task.cancel()
        
    except WebSocketDisconnect:
        logger.info(f"Web终端连接断开: terminal_id={terminal_id}")
    except Exception as e:
        logger.error(f"Web终端错误: {e}")
        try:
            await websocket.send_json({
                'type': 'error',
                'message': str(e)
            })
        except:
            pass
    finally:
        # 清理资源
        if terminal_id:
            web_terminal_manager.close_terminal(terminal_id)
        
        try:
            await websocket.close()
        except:
            pass
