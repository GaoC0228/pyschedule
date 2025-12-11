import React, { useState, useEffect } from 'react';
import {
  Card, Table, Button, Space, Tag, Drawer, Modal, DatePicker, Select, Input,
  message, Tooltip, Descriptions, List, Typography, Divider, Row, Col
} from 'antd';
import {
  SearchOutlined, DownloadOutlined, EyeOutlined, FileTextOutlined,
  ReloadOutlined, ExportOutlined,
  CheckCircleOutlined, CloseCircleOutlined, SyncOutlined, FileOutlined,
  DiffOutlined, CodeSandboxOutlined, PlayCircleOutlined
} from '@ant-design/icons';
import api from '../api/axios';
import dayjs from 'dayjs';
import type { ColumnsType } from 'antd/es/table';

const { RangePicker } = DatePicker;
const { Option } = Select;
const { Text, Paragraph } = Typography;

// 审计日志接口
interface AuditLog {
  id: number;
  username: string;
  user_role: string;
  action: string;
  resource_type: string;
  resource_id?: number;
  script_name?: string;
  script_path?: string;
  status?: string;
  execution_duration?: number;
  files_count: number;
  has_log: boolean;
  ip_address?: string;
  created_at: string;
  details?: string;
}

// 审计文件接口
interface AuditFile {
  id: number;
  file_type: string;
  filename: string;
  file_size: number;
  mime_type?: string;
  is_deleted: boolean;
  deleted_at?: string;
  created_at: string;
  download_url: string;
}

// 审计详情接口
interface AuditDetail extends AuditLog {
  files: AuditFile[];
  execution?: {
    start_time?: string;
    end_time?: string;
    duration?: number;
    status?: string;
    exit_code?: number;
    has_stdout: boolean;
    has_stderr: boolean;
  };
}

const AuditLogs: React.FC = () => {
  // 状态管理
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  // 筛选条件
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null);
  const [filterUsername, setFilterUsername] = useState('');
  const [filterAction, setFilterAction] = useState<string[]>([]);
  const [filterStatus, setFilterStatus] = useState('');

  // 用户列表
  const [users, setUsers] = useState<{username: string; role: string}[]>([]);

  // 详情抽屉
  const [detailVisible, setDetailVisible] = useState(false);
  const [currentDetail, setCurrentDetail] = useState<AuditDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // 日志查看器
  const [logVisible, setLogVisible] = useState(false);
  const [logContent, setLogContent] = useState('');
  const [logLoading, setLogLoading] = useState(false);
  const [logFileRelative, setLogFileRelative] = useState<string | null>(null);
  const [logFileHostPath, setLogFileHostPath] = useState<string | null>(null);
  const [logFileInfo, setLogFileInfo] = useState<any>(null);
  const [isPartialLog, setIsPartialLog] = useState(false);
  const [loadingFullLog, setLoadingFullLog] = useState(false);
  const [currentAuditId, setCurrentAuditId] = useState<number | null>(null);

  // 文件变更查看器
  const [changesVisible, setChangesVisible] = useState(false);
  const [changesData, setChangesData] = useState<any>(null);
  const [changesLoading, setChangesLoading] = useState(false);

  // 加载审计日志列表
  const fetchLogs = async () => {
    setLoading(true);
    try {
      const params: any = {
        page,
        page_size: pageSize,
      };

      if (dateRange) {
        // 后端使用CST时间，直接传递无需时区转换
        params.start_date = dateRange[0].format('YYYY-MM-DD HH:mm:ss');
        params.end_date = dateRange[1].format('YYYY-MM-DD HH:mm:ss');
      }
      if (filterUsername) params.username = filterUsername;
      if (filterAction && filterAction.length > 0) params.action = filterAction.join(',');
      if (filterStatus) params.status = filterStatus;

      const response = await api.get('/audit', { params });
      setLogs(response.data.items);
      setTotal(response.data.total);
    } catch (error) {
      message.error('获取审计日志失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
    fetchLogs();
  }, [page, pageSize]);

  // 获取用户列表
  const fetchUsers = async () => {
    try {
      const response = await api.get('/users/simple');
      setUsers(response.data);
    } catch (error) {
      console.error('获取用户列表失败', error);
    }
  };

  // 查看详情
  const handleViewDetail = async (id: number) => {
    setDetailLoading(true);
    setDetailVisible(true);
    setCurrentAuditId(id);
    try {
      const response = await api.get(`/audit/${id}`);
      setCurrentDetail(response.data);
      
      // 自动加载部分日志（不弹出Modal）
      try {
        const logResponse = await api.get(`/audit/${id}/log`);
        setLogContent(logResponse.data.log_content || '暂无日志');
        setLogFileRelative(logResponse.data.log_file_relative);
        setLogFileHostPath(logResponse.data.log_file_host_path);
        setLogFileInfo(logResponse.data.file_info);
        setIsPartialLog(logResponse.data.is_partial || false);
      } catch (logError) {
        setLogContent('(加载日志失败)');
      }
    } catch (error) {
      message.error('获取详情失败');
    } finally {
      setDetailLoading(false);
    }
  };

  // 查看文件变更
  const handleViewChanges = async (id: number) => {
    setChangesLoading(true);
    setChangesVisible(true);
    try {
      const response = await api.get(`/audit/${id}/file-changes`);
      setChangesData(response.data);
    } catch (error) {
      message.error('获取文件变更失败');
      setChangesVisible(false);
    } finally {
      setChangesLoading(false);
    }
  };

  // 查看执行日志（完整版，弹出Modal）
  const handleViewLog = async (id: number) => {
    setLogLoading(true);
    setLogVisible(true);
    setCurrentAuditId(id);
    try {
      // 加载全部日志
      const response = await api.get(`/audit/${id}/log`, {
        params: { full: true }
      });
      setLogContent(response.data.log_content || '暂无日志');
      setLogFileRelative(response.data.log_file_relative);
      setIsPartialLog(false); // 全部日志，不是部分
    } catch (error) {
      message.error('获取日志失败');
      setLogContent('获取日志失败');
    } finally {
      setLogLoading(false);
    }
  };

  // 加载全部日志
  const handleLoadFullLog = async () => {
    if (!currentAuditId) return;
    setLoadingFullLog(true);
    try {
      const response = await api.get(`/audit/${currentAuditId}/log`, {
        params: { full: true }
      });
      setLogContent(response.data.log_content || '暂无日志');
      setIsPartialLog(false);
      message.success('已加载全部日志');
    } catch (error) {
      message.error('加载全部日志失败');
    } finally {
      setLoadingFullLog(false);
    }
  };

  // 下载文件
  const handleDownloadFile = async (fileId: number, filename: string) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/audit/files/${fileId}/download`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error('下载失败');
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      message.success(`下载成功: ${filename}`);
    } catch (error) {
      message.error('下载失败，请重试');
    }
  };

  // 导出审计日志
  const handleExport = async () => {
    try {
      const params: any = {};
      if (dateRange) {
        params.start_date = dateRange[0].format('YYYY-MM-DD');
        params.end_date = dateRange[1].format('YYYY-MM-DD');
      }
      if (filterUsername) params.username = filterUsername;
      if (filterAction) params.action = filterAction;

      const response = await api.post('/audit/export', null, {
        params: { ...params, format: 'csv' },
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `audit_logs_${dayjs().format('YYYYMMDDHHmmss')}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      message.success('导出成功');
    } catch (error) {
      message.error('导出失败');
    }
  };

  // 搜索
  const handleSearch = () => {
    setPage(1);
    fetchLogs();
  };

  // 重置筛选
  const handleReset = () => {
    setDateRange(null);
    setFilterUsername('');
    setFilterAction([]);
    setFilterStatus('');
    setPage(1);
    fetchLogs();
  };

  // 表格列定义
  const columns: ColumnsType<AuditLog> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 70,
    },
    {
      title: '用户',
      dataIndex: 'username',
      key: 'username',
      width: 120,
      render: (username, record) => (
        <div>
          <div><Text strong>{username}</Text></div>
          <div><Text type="secondary" style={{ fontSize: 12 }}>{record.user_role}</Text></div>
        </div>
      ),
    },
    {
      title: '操作',
      dataIndex: 'action',
      key: 'action',
      width: 150,
      render: (action) => <Tag color="blue">{action}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        if (!status) return '-';
        const statusConfig: Record<string, { icon: React.ReactNode; color: string; text: string }> = {
          success: { icon: <CheckCircleOutlined />, color: 'success', text: '成功' },
          failed: { icon: <CloseCircleOutlined />, color: 'error', text: '失败' },
          running: { icon: <SyncOutlined spin />, color: 'processing', text: '运行中' },
        };
        const config = statusConfig[status] || { icon: null, color: 'default', text: status };
        return <Tag icon={config.icon} color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '执行方式',
      key: 'trigger_type',
      width: 110,
      render: (_, record) => {
        if (!record.details) return '-';
        try {
          const detailObj = typeof record.details === 'string' ? JSON.parse(record.details) : record.details;
          const triggerType = detailObj.trigger_type;
          if (triggerType === 'interactive') {
            return <Tag color="purple" icon={<CodeSandboxOutlined />}>交互式</Tag>;
          } else if (triggerType === 'manual') {
            return <Tag color="cyan" icon={<PlayCircleOutlined />}>非交互式</Tag>;
          }
        } catch {
          // 忽略解析错误
        }
        return '-';
      },
    },
    {
      title: '操作详情',
      key: 'details',
      width: 300,
      ellipsis: true,
      render: (_, record) => {
        const info: string[] = [];
        
        // 解析details字段
        let detailObj: any = null;
        if (record.details) {
          try {
            detailObj = typeof record.details === 'string' ? JSON.parse(record.details) : record.details;
          } catch {
            // 解析失败
          }
        }
        
        // 上传/下载文件：优先显示文件名
        if (record.action === '上传文件' || record.action === '下载文件') {
          if (detailObj?.filename) {
            info.push(`文件: ${detailObj.filename}`);
            if (detailObj.readable_size) {
              info.push(detailObj.readable_size);
            } else if (detailObj.size !== undefined) {
              info.push(`${(detailObj.size / 1024).toFixed(2)} KB`);
            }
          }
        } 
        // 脚本相关信息
        else if (record.script_name) {
          info.push(`脚本: ${record.script_name}`);
        }
        
        // 数据库配置相关信息
        if (record.action.includes('数据库配置') || record.action.includes('数据库连接')) {
          if (detailObj?.config_name) {
            info.push(`配置: ${detailObj.config_name}`);
          }
          if (detailObj?.db_type) {
            info.push(`类型: ${detailObj.db_type}`);
          }
          if (detailObj?.test_result) {
            info.push(`测试: ${detailObj.test_result}`);
          }
          
          // 显示变更详情
          if (detailObj?.changes && Object.keys(detailObj.changes).length > 0) {
            const changeList = Object.entries(detailObj.changes).map(([field, change]: [string, any]) => {
              return `${field}: ${change.old || '空'} → ${change.new || '空'}`;
            });
            info.push(...changeList);
          }
          
          if (detailObj?.message) {
            info.push(detailObj.message);
          }
        }
        
        // 其他详情
        if (detailObj && info.length === 0) {
          if (detailObj.file_path) info.push(`文件: ${detailObj.file_path}`);
          if (detailObj.size !== undefined) info.push(`大小: ${(detailObj.size / 1024).toFixed(2)}KB`);
          if (detailObj.old_path && detailObj.new_path) {
            info.push(`${detailObj.old_path} → ${detailObj.new_path}`);
          }
          if (detailObj.returncode !== undefined) info.push(`退出码: ${detailObj.returncode}`);
          if (detailObj.lines_added !== undefined || detailObj.lines_deleted !== undefined) {
            info.push(`变更: +${detailObj.lines_added || 0}/-${detailObj.lines_deleted || 0}`);
          }
        }
        
        // 如果还是没有信息，尝试显示原文
        if (info.length === 0 && record.details) {
          if (typeof record.details === 'string' && record.details.length < 50) {
            info.push(record.details);
          }
        }
        
        if (info.length === 0) return <Text type="secondary">-</Text>;
        
        const text = info.join(' | ');
        return (
          <Tooltip title={text}>
            <Text ellipsis style={{ fontSize: 12 }}>
              {text}
            </Text>
          </Tooltip>
        );
      },
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (time) => {
        // 后端返回CST时间，直接显示
        return time;
      },
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right',
      width: 200,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record.id)}
          >
            详情
          </Button>
          {record.has_log && (
            <Button
              type="link"
              size="small"
              icon={<FileTextOutlined />}
              onClick={() => handleViewLog(record.id)}
            >
              日志
            </Button>
          )}
          {(record.action === '更新文件' || record.action === '上传文件') && (
            <Button
              type="link"
              size="small"
              icon={<DiffOutlined />}
              onClick={() => handleViewChanges(record.id)}
            >
              变更
            </Button>
          )}
        </Space>
      ),
    },
  ];

  // 格式化文件大小
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div style={{ padding: 24 }}>
      <Card title="审计日志管理" extra={
        <Space>
          <Button icon={<ExportOutlined />} onClick={handleExport}>导出</Button>
          <Button icon={<ReloadOutlined />} onClick={fetchLogs}>刷新</Button>
        </Space>
      }>
        {/* 筛选器 */}
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={8}>
            <RangePicker
              showTime
              format="YYYY-MM-DD HH:mm:ss"
              style={{ width: '100%' }}
              value={dateRange}
              onChange={(dates) => setDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs] | null)}
              placeholder={['开始时间', '结束时间']}
              presets={[
                { label: '最近5分钟', value: [dayjs().subtract(5, 'minute'), dayjs()] },
                { label: '最近15分钟', value: [dayjs().subtract(15, 'minute'), dayjs()] },
                { label: '最近1小时', value: [dayjs().subtract(1, 'hour'), dayjs()] },
                { label: '今天', value: [dayjs().startOf('day'), dayjs().endOf('day')] },
                { label: '最近7天', value: [dayjs().subtract(6, 'day').startOf('day'), dayjs().endOf('day')] },
                { label: '最近30天', value: [dayjs().subtract(29, 'day').startOf('day'), dayjs().endOf('day')] },
                { label: '本月', value: [dayjs().startOf('month'), dayjs().endOf('month')] },
              ]}
            />
          </Col>
          <Col span={4}>
            <Select
              placeholder="选择用户"
              value={filterUsername || undefined}
              onChange={setFilterUsername}
              allowClear
              showSearch
              style={{ width: '100%' }}
              filterOption={(input, option) =>
                String(option?.children || '').toLowerCase().includes(input.toLowerCase())
              }
            >
              {users.map(user => (
                <Option key={user.username} value={user.username}>
                  {user.username} ({user.role === 'admin' ? '管理员' : '普通用户'})
                </Option>
              ))}
            </Select>
          </Col>
          <Col span={4}>
            <Select
              mode="multiple"
              placeholder="操作类型（可多选）"
              value={filterAction}
              onChange={setFilterAction}
              allowClear
              style={{ width: '100%' }}
              showSearch
              maxTagCount="responsive"
            >
              <Option value="用户登录">用户登录</Option>
              <Option value="用户登出">用户登出</Option>
              <Option value="登录失败">登录失败</Option>
              <Option value="上传文件">上传文件</Option>
              <Option value="下载文件">下载文件</Option>
              <Option value="创建文件">创建文件</Option>
              <Option value="更新文件">更新文件</Option>
              <Option value="删除文件">删除文件</Option>
              <Option value="重命名文件">重命名文件</Option>
              <Option value="读取文件">读取文件</Option>
              <Option value="执行脚本">执行脚本</Option>
              <Option value="创建用户">创建用户</Option>
              <Option value="更新用户">更新用户</Option>
              <Option value="删除用户">删除用户</Option>
              <Option value="创建任务">创建任务</Option>
              <Option value="更新任务">更新任务</Option>
              <Option value="删除任务">删除任务</Option>
              <Option value="创建数据库配置">创建数据库配置</Option>
              <Option value="更新数据库配置">更新数据库配置</Option>
              <Option value="删除数据库配置">删除数据库配置</Option>
              <Option value="测试数据库连接">测试数据库连接</Option>
            </Select>
          </Col>
          <Col span={4}>
            <Input
              placeholder="搜索脚本名/路径等"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              allowClear
              prefix={<SearchOutlined />}
            />
          </Col>
          <Col span={4}>
            <Space>
              <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
                搜索
              </Button>
              <Button onClick={handleReset}>重置</Button>
            </Space>
          </Col>
        </Row>

        {/* 数据表格 */}
        <Table
          columns={columns}
          dataSource={logs}
          rowKey="id"
          loading={loading}
          pagination={{
            current: page,
            pageSize: pageSize,
            total: total,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条记录`,
            onChange: (page, pageSize) => {
              setPage(page);
              setPageSize(pageSize);
            },
          }}
          scroll={{ x: 1410 }}
        />
      </Card>

      {/* 详情抽屉 */}
      <Drawer
        title={`审计详情 #${currentDetail?.id || ''}`}
        placement="right"
        width={720}
        onClose={() => setDetailVisible(false)}
        open={detailVisible}
        loading={detailLoading}
      >
        {currentDetail && (() => {
          // 判断是否是脚本相关操作
          const isScriptRelated = ['执行脚本', '创建任务', '更新任务'].includes(currentDetail.action);
          // 判断是否有执行结果
          const hasExecutionInfo = currentDetail.status || currentDetail.execution_duration;
          
          return (
          <div>
            {/* 基本信息 */}
            <Descriptions title="基本信息" bordered column={2} size="small">
              <Descriptions.Item label="用户">{currentDetail.username}</Descriptions.Item>
              <Descriptions.Item label="角色">{currentDetail.user_role}</Descriptions.Item>
              <Descriptions.Item label="操作">
                <Tag color="blue">{currentDetail.action}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="资源类型">{currentDetail.resource_type}</Descriptions.Item>
              
              {/* 只在脚本相关操作时显示脚本信息 */}
              {isScriptRelated && currentDetail.script_name && (
                <Descriptions.Item label="脚本名称" span={2}>
                  <Text code>{currentDetail.script_name}</Text>
                </Descriptions.Item>
              )}
              
              {/* 只在有执行状态时显示 */}
              {hasExecutionInfo && currentDetail.status && (
                <Descriptions.Item label="执行状态">
                  <Tag color={currentDetail.status === 'success' ? 'success' : 'error'}>
                    {currentDetail.status === 'success' ? '成功' : '失败'}
                  </Tag>
                </Descriptions.Item>
              )}
              
              {hasExecutionInfo && currentDetail.execution_duration && (
                <Descriptions.Item label="执行时长">
                  {currentDetail.execution_duration.toFixed(2)}秒
                </Descriptions.Item>
              )}
              
              <Descriptions.Item label="IP地址">{currentDetail.ip_address || '-'}</Descriptions.Item>
              <Descriptions.Item label="操作时间">
                {currentDetail.created_at}
              </Descriptions.Item>
            </Descriptions>

            {/* 执行信息 - 只在有执行数据时显示 */}
            {currentDetail.execution && currentDetail.execution.start_time && (
              <>
                <Divider />
                <Descriptions title="执行信息" bordered column={2} size="small">
                  <Descriptions.Item label="开始时间">
                    {currentDetail.execution.start_time || '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label="结束时间">
                    {currentDetail.execution.end_time || '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label="执行状态">
                    {currentDetail.execution.status ? (
                      <Tag color={currentDetail.execution.status === 'success' ? 'success' : 'error'}>
                        {currentDetail.execution.status}
                      </Tag>
                    ) : '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label="退出码">
                    {currentDetail.execution.exit_code !== undefined ? currentDetail.execution.exit_code : '-'}
                  </Descriptions.Item>
                </Descriptions>
              </>
            )}

            {/* 执行日志预览 - 只要有脚本名就显示 */}
            {currentDetail.script_name && (
              <>
                <Divider />
                <div>
                  <Text strong style={{ fontSize: 16 }}>执行日志</Text>
                  
                  {/* 日志文件详细信息 */}
                  {logFileHostPath && (
                    <div style={{ 
                      marginTop: 16, 
                      marginBottom: 16, 
                      padding: 12, 
                      background: '#f5f5f5', 
                      borderRadius: 4,
                      border: '1px solid #d9d9d9'
                    }}>
                      <div style={{ marginBottom: 8 }}>
                        <Text strong style={{ color: '#1890ff' }}>📁 宿主机路径：</Text>
                        <Text code style={{ fontSize: 13, marginLeft: 8 }}>{logFileHostPath}</Text>
                      </div>
                      
                      {logFileInfo && logFileInfo.exists && (
                        <>
                          <div style={{ display: 'flex', gap: 24, marginTop: 8, flexWrap: 'wrap' }}>
                            <div>
                              <Text type="secondary">文件大小：</Text>
                              <Text strong style={{ marginLeft: 4 }}>
                                {logFileInfo.size_mb > 1 
                                  ? `${logFileInfo.size_mb} MB` 
                                  : `${logFileInfo.size_kb} KB`}
                              </Text>
                            </div>
                            
                            {logFileInfo.line_count && (
                              <div>
                                <Text type="secondary">行数：</Text>
                                <Text strong style={{ marginLeft: 4 }}>{logFileInfo.line_count.toLocaleString()} 行</Text>
                              </div>
                            )}
                            
                            <div>
                              <Text type="secondary">创建时间：</Text>
                              <Text strong style={{ marginLeft: 4 }}>{logFileInfo.created_at}</Text>
                            </div>
                            
                            <div>
                              <Text type="secondary">修改时间：</Text>
                              <Text strong style={{ marginLeft: 4 }}>{logFileInfo.modified_at}</Text>
                            </div>
                          </div>
                        </>
                      )}
                    </div>
                  )}
                  
                  {/* 日志内容预览 */}
                  <div style={{ 
                    background: '#000', 
                    color: '#0f0', 
                    padding: 12, 
                    borderRadius: 4, 
                    fontFamily: 'monospace',
                    fontSize: 12,
                    maxHeight: 300,
                    overflow: 'auto'
                  }}>
                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                      {logContent || '加载中...'}
                    </pre>
                  </div>
                </div>
              </>
            )}

            {/* 生成文件列表 */}
            {currentDetail.files && currentDetail.files.length > 0 && (
              <>
                <Divider />
                <div>
                  <Text strong>生成文件 ({currentDetail.files.length}个)</Text>
                  <List
                    style={{ marginTop: 16 }}
                    bordered
                    dataSource={currentDetail.files}
                    renderItem={(file) => (
                      <List.Item
                        actions={[
                          <Button
                            key="download"
                            type="primary"
                            size="small"
                            icon={<DownloadOutlined />}
                            onClick={() => handleDownloadFile(file.id, file.filename)}
                          >
                            下载
                          </Button>
                        ]}
                      >
                        <List.Item.Meta
                          avatar={<FileOutlined style={{ fontSize: 24 }} />}
                          title={
                            <Space>
                              <Text>{file.filename}</Text>
                              {file.is_deleted && <Tag color="red">已删除</Tag>}
                            </Space>
                          }
                          description={
                            <Space split="|">
                              <Text type="secondary">{file.file_type}</Text>
                              <Text type="secondary">{formatFileSize(file.file_size)}</Text>
                              <Text type="secondary">{file.created_at}</Text>
                            </Space>
                          }
                        />
                      </List.Item>
                    )}
                  />
                </div>
              </>
            )}

            {/* 执行日志查看按钮 */}
            {currentDetail.details && (() => {
              try {
                const details = typeof currentDetail.details === 'string' 
                  ? JSON.parse(currentDetail.details) 
                  : currentDetail.details;
                
                // 如果有log_file，显示查看日志按钮
                if (details.log_file) {
                  return (
                    <>
                      <Divider />
                      <div>
                        <Text strong>执行日志</Text>
                        <div style={{ marginTop: 12 }}>
                          <Button
                            type="primary"
                            icon={<FileTextOutlined />}
                            onClick={() => handleViewLog(currentDetail.id)}
                          >
                            查看完整日志
                          </Button>
                          <Text type="secondary" style={{ marginLeft: 12 }}>
                            日志类型: {details.trigger_type === 'interactive' ? '交互式' : '非交互式'}
                          </Text>
                        </div>
                      </div>
                    </>
                  );
                }
              } catch (e) {
                // 如果解析失败，显示原始信息
              }
              
              // 显示原始详细信息
              return (
                <>
                  <Divider />
                  <div>
                    <Text strong>详细信息</Text>
                    <Paragraph style={{ marginTop: 8 }}>
                      <pre style={{ background: '#f5f5f5', padding: 12, borderRadius: 4 }}>
                        {currentDetail.details}
                      </pre>
                    </Paragraph>
                  </div>
                </>
              );
            })()}
          </div>
          );
        })()}
      </Drawer>

      {/* 日志查看器 */}
      <Modal
        title="执行日志"
        open={logVisible}
        onCancel={() => setLogVisible(false)}
        width={900}
        footer={[
          <Button key="copy" onClick={() => {
            navigator.clipboard.writeText(logContent);
            message.success('已复制到剪贴板');
          }}>
            复制
          </Button>,
          isPartialLog && (
            <Button 
              key="loadFull" 
              type="primary"
              loading={loadingFullLog}
              onClick={handleLoadFullLog}
            >
              查看全部日志
            </Button>
          ),
          <Button key="close" type="primary" onClick={() => setLogVisible(false)}>
            关闭
          </Button>,
        ]}
      >
        {logFileRelative && (
          <div style={{ marginBottom: 16 }}>
            <Text strong>日志文件:</Text>{' '}
            <Text code style={{ fontSize: 12 }}>{logFileRelative}</Text>
          </div>
        )}
        {isPartialLog && (
          <div style={{ marginBottom: 16 }}>
            <div style={{ 
              background: '#e6f7ff', 
              border: '1px solid #91d5ff', 
              borderRadius: 4, 
              padding: '8px 12px',
              fontSize: 14
            }}>
              <span style={{ marginRight: 8 }}>ℹ️</span>
              当前仅显示最后100行日志，如需查看完整日志，请点击下方查看全部日志按钮
            </div>
          </div>
        )}
        <div style={{ maxHeight: 500, overflow: 'auto', background: '#000', color: '#0f0', padding: 16, borderRadius: 4, fontFamily: 'monospace' }}>
          <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
            {logLoading ? '加载中...' : logContent}
          </pre>
        </div>
      </Modal>

      {/* 文件变更对比查看器 */}
      <Modal
        title={<Space><DiffOutlined /> 文件内容变更</Space>}
        open={changesVisible}
        onCancel={() => setChangesVisible(false)}
        width={900}
        footer={[
          <Button key="close" type="primary" onClick={() => setChangesVisible(false)}>
            关闭
          </Button>,
        ]}
      >
        {changesLoading ? (
          <div style={{ textAlign: 'center', padding: 40 }}>加载中...</div>
        ) : changesData ? (
          changesData.has_changes ? (
            <div>
              {/* 变更统计 */}
              <div style={{ marginBottom: 16, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
                <Space size="large">
                  <span>
                    <Text strong>文件数量:</Text> {changesData.file_count}
                  </span>
                  <span>
                    <Text type="success" strong>+{changesData.total_lines_added}</Text> 行新增
                  </span>
                  <span>
                    <Text type="danger" strong>-{changesData.total_lines_deleted}</Text> 行删除
                  </span>
                </Space>
              </div>

              {/* 变更详情 */}
              {changesData.changes.map((change: any) => (
                <div key={change.file_id} style={{ marginBottom: 24 }}>
                  <div style={{ marginBottom: 8, padding: 8, background: '#fafafa', borderRadius: 4 }}>
                    <Space>
                      <FileTextOutlined />
                      <Text strong>{change.file_path}</Text>
                      <Tag color="green">+{change.lines_added}</Tag>
                      <Tag color="red">-{change.lines_deleted}</Tag>
                    </Space>
                  </div>

                  {/* Diff内容 */}
                  <div style={{
                    maxHeight: 400,
                    overflow: 'auto',
                    background: '#1e1e1e',
                    padding: 12,
                    borderRadius: 4,
                    fontFamily: 'monospace',
                    fontSize: 12,
                    lineHeight: 1.6
                  }}>
                    {change.diff_lines.map((line: any, idx: number) => (
                      <div
                        key={idx}
                        style={{
                          padding: '2px 8px',
                          background:
                            line.type === 'added' ? '#1a3d1a' :
                            line.type === 'deleted' ? '#3d1a1a' :
                            line.type === 'info' ? '#1a2332' :
                            'transparent',
                          color:
                            line.type === 'added' ? '#4ade80' :
                            line.type === 'deleted' ? '#f87171' :
                            line.type === 'info' ? '#60a5fa' :
                            '#d1d5db',
                          whiteSpace: 'pre-wrap',
                          wordBreak: 'break-all'
                        }}
                      >
                        <Text style={{
                          color: 'inherit',
                          fontFamily: 'inherit',
                          fontSize: 'inherit'
                        }}>
                          {line.prefix || ''}{line.content}
                        </Text>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: 40 }}>
              <Text type="secondary">{changesData.message || '此操作没有文件内容变更'}</Text>
            </div>
          )
        ) : null}
      </Modal>
    </div>
  );
};

export default AuditLogs;
