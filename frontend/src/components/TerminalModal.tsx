import React, { useEffect, useRef, useState } from 'react';
import { Modal } from 'antd';
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import '@xterm/xterm/css/xterm.css';

interface TerminalModalProps {
  visible: boolean;
  scriptPath: string;
  scriptName: string;
  onClose: () => void;
  onLog?: (message: string) => void;
}

const TerminalModal: React.FC<TerminalModalProps> = ({
  visible,
  scriptPath,
  scriptName,
  onClose,
  onLog
}) => {
  const terminalRef = useRef<HTMLDivElement>(null);
  const [terminal, setTerminal] = useState<Terminal | null>(null);
  const [fitAddon, setFitAddon] = useState<FitAddon | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const sessionIdRef = useRef<string | null>(null);

  useEffect(() => {
    // 只在visible变化且没有terminal时创建，使用sessionId防止重复
    if (!visible || terminal || sessionIdRef.current) {
      return;
    }
    
    if (terminalRef.current) {
      // 生成唯一session_id
      const sessionId = `session_${Date.now()}`;
      sessionIdRef.current = sessionId;
      // 创建终端实例
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

      const fit = new FitAddon();
      term.loadAddon(fit);
      term.open(terminalRef.current);
      fit.fit();

      setTerminal(term);
      setFitAddon(fit);

      // 连接WebSocket（使用已生成的sessionId）
      const token = localStorage.getItem('token');
      
      // 动态获取WebSocket URL（支持域名访问和代理）
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      
      // 判断是否通过代理访问（如Nginx）
      let wsUrl;
      if (host.includes(':3001')) {
        // 直接访问开发服务器
        const apiHost = host.replace(':3001', ':8088');
        wsUrl = `${protocol}//${apiHost}/ws/terminal/${sessionId}?token=${token}`;
      } else {
        // 通过域名/代理访问（如通过Nginx的/python路径）
        const basePath = window.location.pathname.startsWith('/python') ? '/python/api' : '/api';
        wsUrl = `${protocol}//${host}${basePath}/ws/terminal/${sessionId}?token=${token}`;
      }
      
      console.log('WebSocket URL:', wsUrl);
      const websocket = new WebSocket(wsUrl);

      websocket.onopen = () => {
        console.log('WebSocket connected');
        setConnected(true);
        
        // 发送启动命令
        websocket.send(JSON.stringify({
          type: 'start',
          script_path: scriptPath,
          cols: term.cols,
          rows: term.rows
        }));
      };

      websocket.onmessage = (event) => {
        const message = JSON.parse(event.data);
        
        if (message.type === 'output') {
          term.write(message.data);
          // 记录到日志
          if (onLog) {
            onLog(message.data);
          }
        } else if (message.type === 'started') {
          const msg = '终端已启动，脚本正在执行...';
          term.writeln('\r\n\x1b[32m' + msg + '\x1b[0m\r\n');
          if (onLog) {
            onLog('[系统] ' + msg);
          }
        } else if (message.type === 'exit') {
          const msg = '进程已结束';
          term.writeln('\r\n\x1b[33m' + msg + '\x1b[0m\r\n');
          if (onLog) {
            onLog('[系统] ' + msg);
          }
        } else if (message.type === 'error') {
          const msg = `错误: ${message.message}`;
          term.writeln(`\r\n\x1b[31m${msg}\x1b[0m\r\n`);
          if (onLog) {
            onLog('[错误] ' + msg);
          }
        }
      };

      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        term.writeln('\r\n\x1b[31mWebSocket连接错误\x1b[0m\r\n');
      };

      websocket.onclose = () => {
        console.log('WebSocket closed');
        setConnected(false);
      };

      // 处理用户输入
      term.onData((data) => {
        if (websocket.readyState === WebSocket.OPEN) {
          websocket.send(JSON.stringify({
            type: 'input',
            data: data
          }));
        }
      });

      setWs(websocket);

      // 窗口大小变化时调整终端
      const handleResize = () => {
        if (fit) {
          fit.fit();
          if (websocket.readyState === WebSocket.OPEN) {
            websocket.send(JSON.stringify({
              type: 'resize',
              cols: term.cols,
              rows: term.rows
            }));
          }
        }
      };

      window.addEventListener('resize', handleResize);

      return () => {
        sessionIdRef.current = null;
        window.removeEventListener('resize', handleResize);
        if (websocket.readyState === WebSocket.OPEN) {
          websocket.send(JSON.stringify({ type: 'close' }));
          websocket.close();
        }
        term.dispose();
      };
    }
  }, [visible, scriptPath]);

  const handleClose = () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'close' }));
      ws.close();
    }
    if (terminal) {
      terminal.dispose();
      setTerminal(null);
    }
    setConnected(false);
    onClose();
  };

  return (
    <Modal
      title={`交互式终端 - ${scriptName}`}
      open={visible}
      onCancel={handleClose}
      width="80%"
      style={{ top: 20 }}
      footer={null}
      destroyOnClose
    >
      <div
        ref={terminalRef}
        style={{
          height: '500px',
          background: '#000',
          padding: '10px'
        }}
      />
      <div style={{ marginTop: 8, color: '#666', fontSize: 12 }}>
        提示: 这是一个完整的交互式终端，支持输入和输出。按Ctrl+C可以中断脚本。
      </div>
    </Modal>
  );
};

export default TerminalModal;
