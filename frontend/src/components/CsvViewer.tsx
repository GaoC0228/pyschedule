import React, { useMemo, useState } from 'react';
import { Table, Empty } from 'antd';
import type { ColumnsType } from 'antd/es/table';

interface CsvViewerProps {
  content: string;
}

const CsvViewer: React.FC<CsvViewerProps> = ({ content }) => {
  const [pageSize, setPageSize] = useState(10);
  const { columns, dataSource } = useMemo(() => {
    if (!content.trim()) {
      return { columns: [], dataSource: [] };
    }

    const lines = content.split('\n').filter(line => line.trim());
    if (lines.length === 0) {
      return { columns: [], dataSource: [] };
    }

    // 解析CSV（简单实现，支持逗号分隔）
    const parseCSVLine = (line: string): string[] => {
      const result: string[] = [];
      let current = '';
      let inQuotes = false;

      for (let i = 0; i < line.length; i++) {
        const char = line[i];
        
        if (char === '"') {
          inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
          result.push(current.trim());
          current = '';
        } else {
          current += char;
        }
      }
      result.push(current.trim());
      return result;
    };

    // 解析表头
    const headers = parseCSVLine(lines[0]);
    const cols: ColumnsType<any> = headers.map((header, index) => ({
      title: header || `列${index + 1}`,
      dataIndex: `col${index}`,
      key: `col${index}`,
      ellipsis: true,
      width: 150,
    }));

    // 解析数据行
    const data = lines.slice(1).map((line, rowIndex) => {
      const values = parseCSVLine(line);
      const row: any = { key: rowIndex };
      values.forEach((value, colIndex) => {
        row[`col${colIndex}`] = value;
      });
      return row;
    });

    return { columns: cols, dataSource: data };
  }, [content]);

  if (columns.length === 0) {
    return <Empty description="CSV文件为空" />;
  }

  return (
    <div style={{ height: '500px', overflow: 'auto' }}>
      <Table
        columns={columns}
        dataSource={dataSource}
        pagination={{
          pageSize: pageSize,
          showSizeChanger: true,
          pageSizeOptions: ['10', '20', '50', '100'],
          onShowSizeChange: (current, size) => setPageSize(size),
          showTotal: (total) => `共 ${total} 条数据`
        }}
        scroll={{ x: 'max-content', y: 400 }}
        size="small"
        bordered
      />
    </div>
  );
};

export default CsvViewer;
