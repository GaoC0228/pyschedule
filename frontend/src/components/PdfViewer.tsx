import React, { useState, useEffect, useRef } from 'react';
import { Modal, Spin, message, Button, Space, InputNumber } from 'antd';
import { DownloadOutlined, ReloadOutlined, LeftOutlined, RightOutlined } from '@ant-design/icons';
import * as pdfjsLib from 'pdfjs-dist';
import axios from '../api/axios';

// 设置PDF.js的worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;

interface PdfViewerProps {
  visible: boolean;
  filePath: string;
  fileName: string;
  onClose: () => void;
}

const PdfViewer: React.FC<PdfViewerProps> = ({ visible, filePath, fileName, onClose }) => {
  const [loading, setLoading] = useState(false);
  const [pdfDoc, setPdfDoc] = useState<any>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [scale, setScale] = useState(1.5);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (visible && filePath) {
      loadPdfFile();
    }
  }, [visible, filePath]);

  useEffect(() => {
    if (pdfDoc) {
      renderPage(currentPage);
    }
  }, [pdfDoc, currentPage, scale]);

  const loadPdfFile = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/workspace/download', {
        params: { file_path: filePath },
        responseType: 'arraybuffer'
      });

      const loadingTask = pdfjsLib.getDocument({ data: response.data });
      const pdf = await loadingTask.promise;
      
      setPdfDoc(pdf);
      setTotalPages(pdf.numPages);
      setCurrentPage(1);
      
      message.success('PDF文档加载成功');
    } catch (error: any) {
      message.error('加载PDF文档失败: ' + (error.response?.data?.detail || error.message));
      console.error('加载PDF失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderPage = async (pageNum: number) => {
    if (!pdfDoc || !canvasRef.current) return;

    try {
      const page = await pdfDoc.getPage(pageNum);
      const viewport = page.getViewport({ scale });
      
      const canvas = canvasRef.current;
      const context = canvas.getContext('2d');
      
      canvas.height = viewport.height;
      canvas.width = viewport.width;

      const renderContext = {
        canvasContext: context,
        viewport: viewport
      };

      await page.render(renderContext).promise;
    } catch (error) {
      console.error('渲染PDF页面失败:', error);
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

  const goToPrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  const goToNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
    }
  };

  return (
    <Modal
      title={
        <Space>
          <span>PDF查看器 - {fileName}</span>
          <Button
            type="text"
            size="small"
            icon={<ReloadOutlined />}
            onClick={loadPdfFile}
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
        <Space key="pagination">
          <Button icon={<LeftOutlined />} onClick={goToPrevPage} disabled={currentPage <= 1}>
            上一页
          </Button>
          <span>
            第 <InputNumber 
              min={1} 
              max={totalPages} 
              value={currentPage} 
              onChange={(value) => value && setCurrentPage(value)}
              size="small"
              style={{ width: 60 }}
            /> / {totalPages} 页
          </span>
          <Button icon={<RightOutlined />} onClick={goToNextPage} disabled={currentPage >= totalPages}>
            下一页
          </Button>
          <span>缩放: </span>
          <InputNumber 
            min={0.5} 
            max={3} 
            step={0.1}
            value={scale} 
            onChange={(value) => value && setScale(value)}
            size="small"
            style={{ width: 70 }}
            formatter={value => `${(Number(value) * 100).toFixed(0)}%`}
          />
        </Space>,
        <Button key="download" icon={<DownloadOutlined />} onClick={handleDownload}>
          下载文件
        </Button>,
        <Button key="close" onClick={onClose}>
          关闭
        </Button>
      ]}
    >
      <Spin spinning={loading} tip="正在加载PDF文档...">
        <div
          style={{
            maxHeight: '70vh',
            overflowY: 'auto',
            display: 'flex',
            justifyContent: 'center',
            backgroundColor: '#f0f0f0',
            padding: '20px'
          }}
        >
          {pdfDoc ? (
            <canvas ref={canvasRef} style={{ boxShadow: '0 2px 8px rgba(0,0,0,0.15)' }} />
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

export default PdfViewer;
