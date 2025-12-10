import React, { useState, useEffect, useRef } from 'react';
import { Modal, Spin, message, Button, Space } from 'antd';
import { DownloadOutlined, ReloadOutlined } from '@ant-design/icons';
import mammoth from 'mammoth';
import axios from '../api/axios';

interface WordViewerProps {
  visible: boolean;
  filePath: string;
  fileName: string;
  onClose: () => void;
}

const WordViewer: React.FC<WordViewerProps> = ({ visible, filePath, fileName, onClose }) => {
  const [loading, setLoading] = useState(false);
  const [htmlContent, setHtmlContent] = useState('');
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (visible && filePath) {
      loadWordFile();
    }
  }, [visible, filePath]);

  const loadWordFile = async () => {
    setLoading(true);
    try {
      // 下载文件为二进制数据
      const response = await axios.get('/workspace/download', {
        params: { file_path: filePath },
        responseType: 'arraybuffer'
      });

      // 使用mammoth解析Word文档
      const arrayBuffer = response.data;
      const result = await mammoth.convertToHtml({ arrayBuffer });
      
      setHtmlContent(result.value);
      
      if (result.messages.length > 0) {
        console.warn('Word解析警告:', result.messages);
      }
      
      message.success('Word文档加载成功');
    } catch (error: any) {
      message.error('加载Word文档失败: ' + (error.response?.data?.detail || error.message));
      console.error('加载Word失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    try {
      const response = await axios.get('/workspace/download', {
        params: { file_path: filePath },
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', fileName);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      message.success('文件下载成功');
    } catch (error: any) {
      message.error('下载失败');
    }
  };

  return (
    <Modal
      title={
        <Space>
          <span>Word文档查看器 - {fileName}</span>
          <Button
            type="text"
            size="small"
            icon={<ReloadOutlined />}
            onClick={loadWordFile}
            loading={loading}
          >
            刷新
          </Button>
        </Space>
      }
      open={visible}
      onCancel={onClose}
      width="90%"
      style={{ top: 20 }}
      footer={[
        <Button key="download" icon={<DownloadOutlined />} onClick={handleDownload}>
          下载文件
        </Button>,
        <Button key="close" onClick={onClose}>
          关闭
        </Button>
      ]}
    >
      <Spin spinning={loading} tip="正在加载Word文档...">
        <div
          ref={contentRef}
          style={{
            maxHeight: '70vh',
            overflowY: 'auto',
            padding: '20px',
            backgroundColor: '#fff',
            border: '1px solid #d9d9d9',
            borderRadius: '4px'
          }}
        >
          {htmlContent ? (
            <div
              dangerouslySetInnerHTML={{ __html: htmlContent }}
              style={{
                fontFamily: 'Arial, "Microsoft YaHei", sans-serif',
                fontSize: '14px',
                lineHeight: '1.8',
                color: '#333'
              }}
            />
          ) : (
            <div style={{ textAlign: 'center', padding: '50px', color: '#999' }}>
              {loading ? '加载中...' : '暂无内容'}
            </div>
          )}
        </div>
      </Spin>
    </Modal>
  );
};

export default WordViewer;
