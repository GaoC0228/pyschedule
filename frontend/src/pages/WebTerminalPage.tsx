import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Alert, Space } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';
import WebTerminal from '../components/WebTerminal';

const WebTerminalPage: React.FC = () => {
  const navigate = useNavigate();

  const handleClose = () => {
    navigate('/');
  };

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" style={{ width: '100%', marginBottom: '16px' }}>
        <Alert
          message="Web终端使用说明"
          description={
            <ul style={{ marginBottom: 0, paddingLeft: '20px' }}>
              <li>这是一个完整的Shell终端，可以执行任何容器内的命令</li>
              <li>可以使用pip安装Python包：<code>pip install pandas</code></li>
              <li>可以查看和编辑文件：<code>ls /app</code>、<code>cat file.py</code></li>
              <li>可以运行Python脚本进行调试：<code>python script.py</code></li>
              <li>支持Tab自动补全、历史命令（↑↓键）等标准Shell功能</li>
              <li style={{ color: '#ff4d4f' }}>⚠️ 请谨慎操作，避免删除重要文件或修改系统配置</li>
            </ul>
          }
          type="info"
          icon={<InfoCircleOutlined />}
          showIcon
        />
      </Space>
      <WebTerminal onClose={handleClose} />
    </div>
  );
};

export default WebTerminalPage;
