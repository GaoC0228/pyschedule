import React, { useEffect, useRef, useState } from 'react';
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import '@xterm/xterm/css/xterm.css';
import { Card, Button, message, Space, Modal } from 'antd';
import { CloseOutlined, FullscreenOutlined, FullscreenExitOutlined, ReloadOutlined } from '@ant-design/icons';

interface WebTerminalProps {
  onClose?: () => void;
}

const WebTerminal: React.FC<WebTerminalProps> = ({ onClose }) => {
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<Terminal | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  const [connected, setConnected] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const [reconnecting, setReconnecting] = useState(false);

  const connectWebSocket = () => {
    if (!xtermRef.current) return;

    const term = xtermRef.current;
    const token = localStorage.getItem('token');
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/ws/web-terminal?token=${token}&cols=${term.cols}&rows=${term.rows}`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      setReconnecting(false);
      term.writeln('\x1b[1;32m✓ 已连接到容器终端\x1b[0m\r\n');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'error') {
          message.error(data.message);
          term.writeln(`\x1b[1;31m错误: ${data.message}\x1b[0m\r\n`);
        } else if (data.type === 'started') {
          term.writeln(`\x1b[1;32m${data.message}\x1b[0m\r\n`);
        }
      } catch {
        // 普通终端输出
        term.write(event.data);
      }
    };

    ws.onerror = (error) => {
      message.error('WebSocket连接错误');
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      setConnected(false);
      term.writeln('\r\n\x1b[1;31m✗ 连接已断开\x1b[0m');
    };
  };

  useEffect(() => {
    if (!terminalRef.current) return;

    // 创建终端实例
    const term = new Terminal({
      cursorBlink: true,
      fontSize: 14,
      fontFamily: 'Consolas, "Courier New", monospace',
      theme: {
        background: '#1e1e1e',
        foreground: '#cccccc',
        cursor: '#ffffff',
        black: '#000000',
        red: '#cd3131',
        green: '#0dbc79',
        yellow: '#e5e510',
        blue: '#2472c8',
        magenta: '#bc3fbc',
        cyan: '#11a8cd',
        white: '#e5e5e5',
        brightBlack: '#666666',
        brightRed: '#f14c4c',
        brightGreen: '#23d18b',
        brightYellow: '#f5f543',
        brightBlue: '#3b8eea',
        brightMagenta: '#d670d6',
        brightCyan: '#29b8db',
        brightWhite: '#ffffff',
      },
      scrollback: 10000,
      tabStopWidth: 4,
    });

    // 添加插件
    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);

    // 打开终端
    term.open(terminalRef.current);
    fitAddon.fit();

    xtermRef.current = term;
    fitAddonRef.current = fitAddon;

    // 显示欢迎信息
    term.writeln('\x1b[1;32m欢迎使用Web终端\x1b[0m');
    term.writeln('正在连接到容器...\r\n');

    // 建立WebSocket连接
    connectWebSocket();

    // 处理终端输入
    term.onData((data) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(data);
      }
    });

    // 窗口大小调整
    const handleResize = () => {
      if (fitAddonRef.current && xtermRef.current) {
        fitAddonRef.current.fit();
        const { cols, rows } = xtermRef.current;
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({
            type: 'resize',
            cols,
            rows,
          }));
        }
      }
    };

    window.addEventListener('resize', handleResize);

    // 清理
    return () => {
      window.removeEventListener('resize', handleResize);
      if (wsRef.current) {
        wsRef.current.close();
      }
      term.dispose();
    };
  }, []);

  const handleClose = () => {
    Modal.confirm({
      title: '确认关闭',
      content: '关闭终端将断开所有正在运行的命令，确定要关闭吗？',
      onOk: () => {
        if (wsRef.current) {
          wsRef.current.close();
        }
        onClose?.();
      },
    });
  };

  const handleReconnect = () => {
    if (xtermRef.current && !connected && !reconnecting) {
      setReconnecting(true);
      xtermRef.current.writeln('\r\n\x1b[1;33m正在重新连接...\x1b[0m\r\n');
      connectWebSocket();
    }
  };

  const toggleFullscreen = () => {
    setFullscreen(!fullscreen);
    setTimeout(() => {
      fitAddonRef.current?.fit();
    }, 100);
  };

  return (
    <Card
      title={
        <Space>
          <span>🖥️ Web终端</span>
          {connected && <span style={{ color: '#52c41a' }}>● 已连接</span>}
          {!connected && !reconnecting && <span style={{ color: '#ff4d4f' }}>● 未连接</span>}
          {reconnecting && <span style={{ color: '#faad14' }}>● 连接中...</span>}
        </Space>
      }
      extra={
        <Space>
          {!connected && (
            <Button
              icon={<ReloadOutlined />}
              onClick={handleReconnect}
              loading={reconnecting}
            >
              重新连接
            </Button>
          )}
          <Button
            icon={fullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
            onClick={toggleFullscreen}
          >
            {fullscreen ? '退出全屏' : '全屏'}
          </Button>
          <Button danger icon={<CloseOutlined />} onClick={handleClose}>
            关闭
          </Button>
        </Space>
      }
      style={{
        height: fullscreen ? '100vh' : '600px',
        position: fullscreen ? 'fixed' : 'relative',
        top: fullscreen ? 0 : 'auto',
        left: fullscreen ? 0 : 'auto',
        right: fullscreen ? 0 : 'auto',
        bottom: fullscreen ? 0 : 'auto',
        zIndex: fullscreen ? 9999 : 'auto',
        margin: 0,
      }}
      bodyStyle={{
        padding: 0,
        height: 'calc(100% - 57px)',
        backgroundColor: '#1e1e1e',
      }}
    >
      <div
        ref={terminalRef}
        style={{
          height: '100%',
          padding: '10px',
        }}
      />
    </Card>
  );
};

export default WebTerminal;
