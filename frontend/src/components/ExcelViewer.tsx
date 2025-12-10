import React, { useState, useEffect } from 'react';
import { Modal, Table, Tabs, Spin, message, Button, Space } from 'antd';
import { DownloadOutlined, ReloadOutlined } from '@ant-design/icons';
import * as XLSX from 'xlsx';
import axios from '../api/axios';

interface ExcelViewerProps {
  visible: boolean;
  filePath: string;
  fileName: string;
  onClose: () => void;
}

interface SheetData {
  name: string;
  data: any[];
  columns: any[];
}

const ExcelViewer: React.FC<ExcelViewerProps> = ({ visible, filePath, fileName, onClose }) => {
  const [loading, setLoading] = useState(false);
  const [sheets, setSheets] = useState<SheetData[]>([]);
  const [activeSheet, setActiveSheet] = useState('0');

  useEffect(() => {
    if (visible && filePath) {
      loadExcelFile();
    }
  }, [visible, filePath]);

  const loadExcelFile = async () => {
    setLoading(true);
    try {
      // 下载文件为二进制数据
      const response = await axios.get('/workspace/download', {
        params: { file_path: filePath },
        responseType: 'arraybuffer'
      });

      // 使用SheetJS解析Excel
      const data = new Uint8Array(response.data);
      const workbook = XLSX.read(data, { type: 'array' });

      // 转换所有工作表
      const sheetsData: SheetData[] = workbook.SheetNames.map((sheetName) => {
        const worksheet = workbook.Sheets[sheetName];
        const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });

        // 如果数据为空
        if (jsonData.length === 0) {
          return {
            name: sheetName,
            data: [],
            columns: []
          };
        }

        // 第一行作为列名
        const headers = jsonData[0] as any[];
        const rows = jsonData.slice(1) as any[];

        // 生成列定义
        const columns = headers.map((header, index) => ({
          title: header || `列${index + 1}`,
          dataIndex: `col${index}`,
          key: `col${index}`,
          width: 150,
          ellipsis: true,
        }));

        // 转换数据格式
        const data = rows.map((row, rowIndex) => {
          const record: any = { key: rowIndex };
          headers.forEach((_, colIndex) => {
            record[`col${colIndex}`] = row[colIndex] !== undefined ? String(row[colIndex]) : '';
          });
          return record;
        });

        return {
          name: sheetName,
          data,
          columns
        };
      });

      setSheets(sheetsData);
      setActiveSheet('0');
      message.success('Excel文件加载成功');
    } catch (error: any) {
      message.error('加载Excel文件失败: ' + (error.response?.data?.detail || error.message));
      console.error('加载Excel失败:', error);
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

  const tabItems = sheets.map((sheet, index) => ({
    key: String(index),
    label: sheet.name,
    children: (
      <Table
        columns={sheet.columns}
        dataSource={sheet.data}
        pagination={{
          pageSize: 20,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 行数据`
        }}
        scroll={{ x: 'max-content', y: 450 }}
        size="small"
        bordered
      />
    )
  }));

  return (
    <Modal
      title={
        <Space>
          <span>Excel查看器 - {fileName}</span>
          <Button
            type="text"
            size="small"
            icon={<ReloadOutlined />}
            onClick={loadExcelFile}
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
      <Spin spinning={loading} tip="正在加载Excel文件...">
        {sheets.length > 0 ? (
          <Tabs
            activeKey={activeSheet}
            onChange={setActiveSheet}
            items={tabItems}
          />
        ) : (
          <div style={{ textAlign: 'center', padding: '50px', color: '#999' }}>
            暂无数据
          </div>
        )}
      </Spin>
    </Modal>
  );
};

export default ExcelViewer;
