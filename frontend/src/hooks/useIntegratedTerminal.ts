import { useEffect, useRef } from 'react';
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import '@xterm/xterm/css/xterm.css';

interface UseIntegratedTerminalProps {
  containerRef: React.RefObject<HTMLDivElement>;
  scriptPath: string;
  onOutput: (text: string) => void;
  onExit: () => void;
}

export const useIntegratedTerminal = ({
  containerRef,
  scriptPath,
  onOutput,
  onExit
}: UseIntegratedTerminalProps) => {
  const terminalRef = useRef<Terminal | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!containerRef.current || !scriptPath) return;

    // 创建终端
    const term = new Terminal({
      cursorBlink: true,
      fontSize: 14,
      fontFamily: 'Consolas, Monaco, "Courier New", monospace',
      theme: {
        background: '#000000',
        foreground: '#00ff00',
      },
      rows: 24,
      cols: 80
    });

    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    term.open(containerRef.current);
    fitAddon.fit();

    terminalRef.current = term;

    // 连接WebSocket
    const token = localStorage.getItem('token');
    const sessionId = `session_${Date.now()}`;
    const wsUrl = `ws://localhost:8088/ws/terminal/${sessionId}?token=${token}`;
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      onOutput('[系统] 交互式终端已连接\n');
      
      // 发送启动命令
      ws.send(JSON.stringify({
        type: 'start',
        script_path: scriptPath,
        cols: term.cols,
        rows: term.rows
      }));
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      if (message.type === 'output') {
        term.write(message.data);
        onOutput(message.data);
      } else if (message.type === 'started') {
        const msg = '[系统] 脚本开始执行...\n';
        term.writeln('\r\n\x1b[32m' + msg + '\x1b[0m');
        onOutput(msg);
      } else if (message.type === 'exit') {
        const msg = '[系统] 脚本执行完成\n';
        term.writeln('\r\n\x1b[33m' + msg + '\x1b[0m');
        onOutput(msg);
        setTimeout(() => onExit(), 1000);
      } else if (message.type === 'error') {
        const msg = `[错误] ${message.message}\n`;
        term.writeln('\r\n\x1b[31m' + msg + '\x1b[0m');
        onOutput(msg);
      }
    };

    ws.onerror = () => {
      const msg = '[错误] WebSocket连接失败\n';
      term.writeln('\r\n\x1b[31m' + msg + '\x1b[0m');
      onOutput(msg);
    };

    ws.onclose = () => {
      onOutput('[系统] 连接已关闭\n');
    };

    // 处理用户输入
    term.onData((data) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          type: 'input',
          data: data
        }));
      }
    });

    // 清理函数
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'close' }));
        ws.close();
      }
      term.dispose();
    };
  }, [containerRef, scriptPath, onOutput, onExit]);

  return {
    terminal: terminalRef.current,
    websocket: wsRef.current
  };
};
