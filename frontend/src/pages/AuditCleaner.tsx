import React, { useState, useEffect } from 'react';
import {
  Card, Row, Col, Statistic, Button, Space, Modal, InputNumber, Select,
  message, Spin, Alert, Tag, Divider
} from 'antd';
import {
  DeleteOutlined, WarningOutlined, ReloadOutlined,
  FileTextOutlined, DatabaseOutlined, ClockCircleOutlined
} from '@ant-design/icons';
import api from '../api/axios';

const { Option } = Select;

const AuditCleaner: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<any>(null);
  const [cleanModalVisible, setCleanModalVisible] = useState(false);
  const [cleanType, setCleanType] = useState<'days' | 'count'>('days');
  const [days, setDays] = useState(90);
  const [keepCount, setKeepCount] = useState(10000);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);

  // 加载统计信息
  const loadStatistics = async () => {
    setLoading(true);
    try {
      const response = await api.get('/audit-cleaner/statistics');
      if (response.data.success) {
        setStats(response.data.data);
      }
    } catch (error: any) {
      message.error('加载统计信息失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStatistics();
  }, []);

  // 按天数清理
  const handleCleanByDays = async () => {
    Modal.confirm({
      title: '确认清理',
      icon: <WarningOutlined />,
      content: (
        <div>
          <p>即将删除 <strong>{days}天前</strong> 的审计日志</p>
          {statusFilter && <p>状态过滤: <Tag>{statusFilter}</Tag></p>}
          <Alert
            message="此操作不可恢复"
            description="删除的数据库记录和日志文件将无法恢复"
            type="warning"
            showIcon
            style={{ marginTop: 12 }}
          />
        </div>
      ),
      okText: '确认清理',
      cancelText: '取消',
      okButtonProps: { danger: true },
      onOk: async () => {
        setLoading(true);
        try {
          const response = await api.post('/audit-cleaner/clean-by-days', {
            days,
            status: statusFilter
          });
          if (response.data.success) {
            message.success(response.data.message);
            loadStatistics();
          }
        } catch (error: any) {
          message.error('清理失败: ' + (error.response?.data?.detail || error.message));
        } finally {
          setLoading(false);
          setCleanModalVisible(false);
        }
      }
    });
  };

  // 按数量清理
  const handleCleanByCount = async () => {
    Modal.confirm({
      title: '确认清理',
      icon: <WarningOutlined />,
      content: (
        <div>
          <p>只保留最新的 <strong>{keepCount}条</strong> 记录</p>
          <p>当前记录总数: <strong>{stats?.total_logs || 0}</strong></p>
          <p>将删除: <strong>{Math.max(0, (stats?.total_logs || 0) - keepCount)}</strong> 条记录</p>
          <Alert
            message="此操作不可恢复"
            description="删除的数据库记录和日志文件将无法恢复"
            type="warning"
            showIcon
            style={{ marginTop: 12 }}
          />
        </div>
      ),
      okText: '确认清理',
      cancelText: '取消',
      okButtonProps: { danger: true },
      onOk: async () => {
        setLoading(true);
        try {
          const response = await api.post('/audit-cleaner/clean-by-count', {
            keep_count: keepCount
          });
          if (response.data.success) {
            message.success(response.data.message);
            loadStatistics();
          }
        } catch (error: any) {
          message.error('清理失败: ' + (error.response?.data?.detail || error.message));
        } finally {
          setLoading(false);
          setCleanModalVisible(false);
        }
      }
    });
  };

  // 清理孤儿文件
  const handleCleanOrphanFiles = async () => {
    Modal.confirm({
      title: '清理孤儿文件',
      icon: <WarningOutlined />,
      content: '清理数据库中没有记录的日志文件，这些文件可能是由于删除操作或异常情况产生的。',
      okText: '确认清理',
      cancelText: '取消',
      onOk: async () => {
        setLoading(true);
        try {
          const response = await api.post('/audit-cleaner/clean-orphan-files');
          if (response.data.success) {
            message.success(response.data.message);
            loadStatistics();
          }
        } catch (error: any) {
          message.error('清理失败: ' + (error.response?.data?.detail || error.message));
        } finally {
          setLoading(false);
        }
      }
    });
  };

  return (
    <div style={{ padding: 24 }}>
      <Card title="审计日志清理" extra={
        <Button icon={<ReloadOutlined />} onClick={loadStatistics} loading={loading}>
          刷新
        </Button>
      }>
        <Spin spinning={loading}>
          {/* 统计信息 */}
          {stats && (
            <>
              <Row gutter={16}>
                <Col span={6}>
                  <Card>
                    <Statistic
                      title="总记录数"
                      value={stats.total_logs}
                      prefix={<DatabaseOutlined />}
                    />
                  </Card>
                </Col>
                <Col span={6}>
                  <Card>
                    <Statistic
                      title="日志文件数"
                      value={stats.log_files.count}
                      prefix={<FileTextOutlined />}
                    />
                  </Card>
                </Col>
                <Col span={6}>
                  <Card>
                    <Statistic
                      title="占用空间"
                      value={stats.log_files.total_size_mb}
                      suffix="MB"
                    />
                  </Card>
                </Col>
                <Col span={6}>
                  <Card>
                    <Statistic
                      title="时间跨度"
                      value={stats.date_range.oldest ? (
                        new Date(stats.date_range.newest).getTime() - 
                        new Date(stats.date_range.oldest).getTime()
                      ) / (1000 * 60 * 60 * 24) : 0}
                      suffix="天"
                      precision={0}
                      prefix={<ClockCircleOutlined />}
                    />
                  </Card>
                </Col>
              </Row>

              <Divider />

              {/* 状态分布 */}
              <Row gutter={16}>
                <Col span={8}>
                  <Card size="small" title="按状态分布">
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span><Tag color="success">成功</Tag></span>
                        <span>{stats.status_breakdown.success}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span><Tag color="error">失败</Tag></span>
                        <span>{stats.status_breakdown.failed}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span><Tag color="processing">运行中</Tag></span>
                        <span>{stats.status_breakdown.running}</span>
                      </div>
                    </Space>
                  </Card>
                </Col>
                <Col span={8}>
                  <Card size="small" title="按类型分布">
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span><Tag color="purple">交互式</Tag></span>
                        <span>{stats.type_breakdown.interactive}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span><Tag color="cyan">非交互式</Tag></span>
                        <span>{stats.type_breakdown.manual}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span><Tag>其他</Tag></span>
                        <span>{stats.type_breakdown.other}</span>
                      </div>
                    </Space>
                  </Card>
                </Col>
                <Col span={8}>
                  <Card size="small" title="日期范围">
                    <Space direction="vertical" style={{ width: '100%', fontSize: 12 }}>
                      <div>
                        <strong>最早:</strong><br />
                        {stats.date_range.oldest ? 
                          new Date(stats.date_range.oldest).toLocaleString('zh-CN') 
                          : '-'}
                      </div>
                      <div>
                        <strong>最新:</strong><br />
                        {stats.date_range.newest ? 
                          new Date(stats.date_range.newest).toLocaleString('zh-CN') 
                          : '-'}
                      </div>
                    </Space>
                  </Card>
                </Col>
              </Row>

              <Divider />

              {/* 清理操作 */}
              <Alert
                message="清理建议"
                description="建议定期清理审计日志以节省存储空间。建议保留最近3-6个月的记录，或保留最新10000条记录。"
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />

              <Space size="large">
                <Button
                  type="primary"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={() => {
                    setCleanType('days');
                    setCleanModalVisible(true);
                  }}
                >
                  按时间清理
                </Button>
                <Button
                  danger
                  icon={<DeleteOutlined />}
                  onClick={() => {
                    setCleanType('count');
                    setCleanModalVisible(true);
                  }}
                >
                  按数量清理
                </Button>
                <Button
                  icon={<FileTextOutlined />}
                  onClick={handleCleanOrphanFiles}
                >
                  清理孤儿文件
                </Button>
              </Space>
            </>
          )}
        </Spin>
      </Card>

      {/* 清理配置Modal */}
      <Modal
        title={cleanType === 'days' ? '按时间清理' : '按数量清理'}
        open={cleanModalVisible}
        onCancel={() => setCleanModalVisible(false)}
        footer={[
          <Button key="cancel" onClick={() => setCleanModalVisible(false)}>
            取消
          </Button>,
          <Button
            key="submit"
            type="primary"
            danger
            onClick={cleanType === 'days' ? handleCleanByDays : handleCleanByCount}
          >
            开始清理
          </Button>,
        ]}
      >
        {cleanType === 'days' ? (
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <label>保留天数:</label>
              <InputNumber
                min={1}
                max={3650}
                value={days}
                onChange={(value) => setDays(value || 90)}
                style={{ width: '100%', marginTop: 8 }}
                addonAfter="天"
              />
              <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
                将删除 {days} 天前的记录
              </div>
            </div>
            <div style={{ marginTop: 16 }}>
              <label>状态过滤 (可选):</label>
              <Select
                placeholder="全部状态"
                allowClear
                value={statusFilter}
                onChange={setStatusFilter}
                style={{ width: '100%', marginTop: 8 }}
              >
                <Option value="success">成功</Option>
                <Option value="failed">失败</Option>
                <Option value="running">运行中</Option>
              </Select>
            </div>
          </Space>
        ) : (
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <label>保留记录数:</label>
              <InputNumber
                min={100}
                max={1000000}
                value={keepCount}
                onChange={(value) => setKeepCount(value || 10000)}
                style={{ width: '100%', marginTop: 8 }}
                addonAfter="条"
              />
              <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
                只保留最新的 {keepCount} 条记录
              </div>
              <div style={{ fontSize: 12, color: '#ff4d4f', marginTop: 4 }}>
                当前: {stats?.total_logs || 0} 条，
                将删除: {Math.max(0, (stats?.total_logs || 0) - keepCount)} 条
              </div>
            </div>
          </Space>
        )}
      </Modal>
    </div>
  );
};

export default AuditCleaner;
