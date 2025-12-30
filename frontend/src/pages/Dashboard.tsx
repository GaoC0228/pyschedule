import { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, Table, Tag, Button, Spin, Descriptions, message } from 'antd'
import { ClockCircleOutlined, CheckCircleOutlined, CloseCircleOutlined, UserOutlined, GlobalOutlined, ReloadOutlined, EnvironmentOutlined } from '@ant-design/icons'
import api from '../api/axios'
import dayjs from 'dayjs'

const Dashboard = () => {
  const [stats, setStats] = useState({ total: 0, active: 0, success: 0, failed: 0 })
  const [recentTasks, setRecentTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [publicIp, setPublicIp] = useState<any>(null)
  const [ipLoading, setIpLoading] = useState(false)

  useEffect(() => {
    fetchData()
    // 从 localStorage 加载缓存的IP信息
    loadCachedIpInfo()
  }, [])

  const fetchData = async () => {
    try {
      const tasksRes = await api.get('/tasks')
      const tasks = tasksRes.data
      
      setStats({
        total: tasks.length,
        active: tasks.filter((t: any) => t.is_active).length,
        success: tasks.filter((t: any) => t.status === 'success').length,
        failed: tasks.filter((t: any) => t.status === 'failed').length,
      })
      
      setRecentTasks(tasks.slice(0, 10))
    } catch (error) {
      console.error('获取数据失败', error)
    } finally {
      setLoading(false)
    }
  }

  // 从 localStorage 加载缓存的IP信息
  const loadCachedIpInfo = () => {
    try {
      const cachedIp = localStorage.getItem('publicIpInfo')
      if (cachedIp) {
        setPublicIp(JSON.parse(cachedIp))
      }
    } catch (error) {
      console.error('加载缓存的IP信息失败', error)
    }
  }

  const fetchPublicIp = async () => {
    setIpLoading(true)
    try {
      const response = await api.get('/system/public-ip')
      if (response.data.success) {
        const ipData = response.data.data
        setPublicIp(ipData)
        // 保存到 localStorage
        localStorage.setItem('publicIpInfo', JSON.stringify(ipData))
        message.success('公网IP信息获取成功')
      }
    } catch (error: any) {
      console.error('获取公网IP失败', error)
      message.error(error.response?.data?.detail || '获取公网IP失败')
      setPublicIp(null)
    } finally {
      setIpLoading(false)
    }
  }

  const statusColors: any = {
    pending: 'default',
    running: 'processing',
    success: 'success',
    failed: 'error',
    paused: 'warning',
  }

  const statusText: any = {
    pending: '待执行',
    running: '运行中',
    success: '成功',
    failed: '失败',
    paused: '已暂停',
  }

  const columns = [
    { title: '任务名称', dataIndex: 'name', key: 'name' },
    { 
      title: '状态', 
      dataIndex: 'status', 
      key: 'status',
      render: (status: string) => (
        <Tag color={statusColors[status]}>{statusText[status]}</Tag>
      )
    },
    { 
      title: '最后运行', 
      dataIndex: 'last_run_at', 
      key: 'last_run_at',
      render: (time: string) => time ? dayjs(time).format('YYYY-MM-DD HH:mm:ss') : '-'
    },
    { 
      title: '下次运行', 
      dataIndex: 'next_run_at', 
      key: 'next_run_at',
      render: (time: string) => time ? dayjs(time).format('YYYY-MM-DD HH:mm:ss') : '-'
    },
  ]

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总任务数"
              value={stats.total}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="活跃任务"
              value={stats.active}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="成功执行"
              value={stats.success}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="执行失败"
              value={stats.failed}
              prefix={<CloseCircleOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 公网IP信息卡片 */}
      <Card 
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <GlobalOutlined style={{ fontSize: 18 }} />
            <span>公网IP信息</span>
          </div>
        }
        extra={
          <Button 
            type="primary" 
            icon={<ReloadOutlined />} 
            onClick={fetchPublicIp}
            loading={ipLoading}
          >
            刷新
          </Button>
        }
        style={{ marginBottom: 24 }}
      >
        {ipLoading ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin tip="正在获取公网IP信息..." />
          </div>
        ) : publicIp ? (
          <Descriptions column={2} bordered>
            <Descriptions.Item label="IP地址">
              <strong style={{ color: '#1890ff', fontSize: 16 }}>{publicIp.ip || '-'}</strong>
            </Descriptions.Item>
            <Descriptions.Item label={<span><EnvironmentOutlined /> 国家</span>}>
              {publicIp.country ? `${publicIp.country} (${publicIp.country_code})` : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="地区">
              {publicIp.region || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="城市">
              {publicIp.city || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="ISP服务商">
              {publicIp.isp || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="组织">
              {publicIp.org || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="时区">
              {publicIp.timezone || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="坐标">
              {publicIp.lat && publicIp.lon ? `${publicIp.lat}, ${publicIp.lon}` : '-'}
            </Descriptions.Item>
          </Descriptions>
        ) : (
          <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
            <GlobalOutlined style={{ fontSize: 48, marginBottom: 16 }} />
            <p>暂无公网IP信息，请点击刷新按钮获取</p>
          </div>
        )}
      </Card>

      <Card title="最近任务" loading={loading}>
        <Table
          dataSource={recentTasks}
          columns={columns}
          rowKey="id"
          pagination={false}
        />
      </Card>
    </div>
  )
}

export default Dashboard
