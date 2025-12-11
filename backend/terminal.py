#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Web终端管理器
支持交互式脚本执行
"""

import os
import pty
import subprocess
import select
import termios
import struct
import fcntl
import signal
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class Terminal:
    """终端会话"""
    
    def __init__(self, workspace_dir: str):
        self.workspace_dir = workspace_dir
        self.fd = None
        self.pid = None
        self.process = None
        
    def spawn(self, script_path: str, cols: int = 80, rows: int = 24):
        """启动终端进程"""
        try:
            # 获取脚本的完整路径
            full_path = os.path.join(self.workspace_dir, script_path)
            
            if not os.path.exists(full_path):
                raise FileNotFoundError(f"脚本不存在: {full_path}")
            
            # 获取脚本所在目录作为工作目录
            work_dir = os.path.dirname(full_path)
            if not work_dir:
                work_dir = self.workspace_dir
            
            # 创建伪终端
            self.pid, self.fd = pty.fork()
            
            if self.pid == 0:
                # 子进程
                os.chdir(work_dir)
                # 设置PYTHONPATH，让脚本可以导入backend的公共模块（如db_configs）
                pythonpath = os.environ.get('PYTHONPATH', '')
                os.environ['PYTHONPATH'] = f"/app:{pythonpath}" if pythonpath else "/app"
                os.execvp('python', ['python', full_path])
            else:
                # 父进程
                # 设置终端大小
                self.resize(cols, rows)
                # 设置非阻塞
                flag = fcntl.fcntl(self.fd, fcntl.F_GETFL)
                fcntl.fcntl(self.fd, fcntl.F_SETFL, flag | os.O_NONBLOCK)
                
                logger.info(f"终端已启动: PID={self.pid}, 脚本={script_path}")
                return True
                
        except Exception as e:
            logger.error(f"启动终端失败: {str(e)}")
            raise
    
    def resize(self, cols: int, rows: int):
        """调整终端大小"""
        if self.fd:
            winsize = struct.pack('HHHH', rows, cols, 0, 0)
            fcntl.ioctl(self.fd, termios.TIOCSWINSZ, winsize)
    
    def write(self, data: str):
        """写入数据到终端"""
        if self.fd:
            try:
                os.write(self.fd, data.encode('utf-8'))
            except OSError as e:
                logger.error(f"写入终端失败: {str(e)}")
    
    def read(self, timeout: float = 0.1) -> bytes:
        """从终端读取数据"""
        if not self.fd:
            return b''
        
        try:
            # 使用select检查是否有数据可读
            ready, _, _ = select.select([self.fd], [], [], timeout)
            if ready:
                return os.read(self.fd, 4096)
        except OSError:
            pass
        
        return b''
    
    def is_alive(self) -> bool:
        """检查进程是否存活"""
        if not self.pid:
            return False
        
        try:
            # 发送信号0检查进程是否存在
            os.kill(self.pid, 0)
            return True
        except OSError:
            return False
    
    def get_exit_status(self) -> int:
        """获取进程退出码（仅在进程结束后调用）"""
        if not self.pid:
            return -1
        
        try:
            # 非阻塞检查进程状态
            pid, status = os.waitpid(self.pid, os.WNOHANG)
            if pid == self.pid:
                # 进程已结束，返回退出码
                return os.WEXITSTATUS(status) if os.WIFEXITED(status) else -1
        except:
            pass
        
        return 0
    
    def kill(self):
        """终止终端进程"""
        if self.pid:
            try:
                os.kill(self.pid, signal.SIGTERM)
                os.waitpid(self.pid, 0)
            except:
                pass
        
        if self.fd:
            try:
                os.close(self.fd)
            except:
                pass
        
        self.pid = None
        self.fd = None
        logger.info("终端已关闭")


class TerminalManager:
    """终端管理器"""
    
    def __init__(self, workspace_dir: str):
        self.workspace_dir = workspace_dir
        self.terminals: Dict[str, Terminal] = {}
    
    def create_terminal(self, session_id: str, script_path: str, cols: int = 80, rows: int = 24) -> Terminal:
        """创建新终端"""
        # 如果已存在，先关闭
        if session_id in self.terminals:
            self.terminals[session_id].kill()
        
        terminal = Terminal(self.workspace_dir)
        terminal.spawn(script_path, cols, rows)
        self.terminals[session_id] = terminal
        
        logger.info(f"创建终端会话: {session_id}")
        return terminal
    
    def get_terminal(self, session_id: str) -> Terminal:
        """获取终端"""
        return self.terminals.get(session_id)
    
    def close_terminal(self, session_id: str):
        """关闭终端"""
        if session_id in self.terminals:
            self.terminals[session_id].kill()
            del self.terminals[session_id]
            logger.info(f"关闭终端会话: {session_id}")
    
    def cleanup_dead_terminals(self):
        """清理已死亡的终端"""
        dead_sessions = []
        for session_id, terminal in self.terminals.items():
            if not terminal.is_alive():
                dead_sessions.append(session_id)
        
        for session_id in dead_sessions:
            self.close_terminal(session_id)
