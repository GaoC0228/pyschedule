#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Web终端管理器 - 提供完整的Shell访问
"""
import os
import pty
import select
import struct
import fcntl
import termios
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class WebTerminal:
    """Web终端会话"""
    
    def __init__(self, terminal_id: str, user_id: int, shell: str = "/bin/bash"):
        self.terminal_id = terminal_id
        self.user_id = user_id
        self.shell = shell
        self.fd = None
        self.pid = None
        self.closed = False
        
    def spawn(self, cols: int = 80, rows: int = 24):
        """启动Shell进程"""
        try:
            # 创建伪终端
            self.pid, self.fd = pty.fork()
            
            if self.pid == 0:
                # 子进程 - 执行shell
                # 设置环境变量
                env = os.environ.copy()
                env['TERM'] = 'xterm-256color'
                env['COLORTERM'] = 'truecolor'
                env['PS1'] = r'\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
                env['PYTHONPATH'] = '/app'
                
                # 执行shell
                os.execvpe(self.shell, [self.shell], env)
            else:
                # 父进程
                # 设置终端大小
                self.resize(cols, rows)
                
                # 设置非阻塞
                flag = fcntl.fcntl(self.fd, fcntl.F_GETFL)
                fcntl.fcntl(self.fd, fcntl.F_SETFL, flag | os.O_NONBLOCK)
                
                logger.info(f"Web终端已启动: terminal_id={self.terminal_id}, pid={self.pid}")
                return True
                
        except Exception as e:
            logger.error(f"启动终端失败: {e}")
            raise
    
    def resize(self, cols: int, rows: int):
        """调整终端大小"""
        if self.fd:
            winsize = struct.pack('HHHH', rows, cols, 0, 0)
            fcntl.ioctl(self.fd, termios.TIOCSWINSZ, winsize)
    
    def write(self, data: str):
        """写入数据到终端"""
        if self.fd and not self.closed:
            try:
                os.write(self.fd, data.encode('utf-8'))
            except OSError as e:
                logger.error(f"写入终端失败: {e}")
                self.closed = True
    
    def read(self, timeout: float = 0.05) -> bytes:
        """从终端读取数据"""
        if not self.fd or self.closed:
            return b''
        
        try:
            # 使用select检查是否有数据可读
            ready, _, _ = select.select([self.fd], [], [], timeout)
            if ready:
                data = os.read(self.fd, 4096)
                if not data:
                    self.closed = True
                return data
        except OSError:
            self.closed = True
        
        return b''
    
    def is_alive(self) -> bool:
        """检查进程是否存活"""
        if not self.pid or self.closed:
            return False
        
        try:
            # 发送信号0检查进程是否存在
            os.kill(self.pid, 0)
            return True
        except OSError:
            return False
    
    def kill(self):
        """终止终端进程"""
        if self.pid:
            try:
                os.kill(self.pid, 9)  # SIGKILL
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
        self.closed = True
        logger.info(f"Web终端已关闭: terminal_id={self.terminal_id}")


class WebTerminalManager:
    """Web终端管理器"""
    
    def __init__(self):
        self.terminals: Dict[str, WebTerminal] = {}
    
    def create_terminal(self, terminal_id: str, user_id: int, cols: int = 80, rows: int = 24) -> WebTerminal:
        """创建新终端"""
        # 如果已存在，先关闭
        if terminal_id in self.terminals:
            self.terminals[terminal_id].kill()
        
        terminal = WebTerminal(terminal_id, user_id)
        terminal.spawn(cols, rows)
        self.terminals[terminal_id] = terminal
        
        logger.info(f"创建Web终端: terminal_id={terminal_id}, user_id={user_id}")
        return terminal
    
    def get_terminal(self, terminal_id: str) -> Optional[WebTerminal]:
        """获取终端"""
        return self.terminals.get(terminal_id)
    
    def close_terminal(self, terminal_id: str):
        """关闭终端"""
        if terminal_id in self.terminals:
            self.terminals[terminal_id].kill()
            del self.terminals[terminal_id]
            logger.info(f"已关闭Web终端: terminal_id={terminal_id}")
    
    def cleanup_dead_terminals(self):
        """清理已死亡的终端"""
        dead_terminals = []
        for terminal_id, terminal in self.terminals.items():
            if not terminal.is_alive():
                dead_terminals.append(terminal_id)
        
        for terminal_id in dead_terminals:
            self.close_terminal(terminal_id)


# 全局终端管理器实例
web_terminal_manager = WebTerminalManager()
