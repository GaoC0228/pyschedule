import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Table, Button, Space, Tag, Modal, Form, Input, Upload, message, Drawer, Tabs, Switch as AntSwitch, Select, Alert } from 'antd'
import { PlusOutlined, PlayCircleOutlined, EditOutlined, DeleteOutlined, UploadOutlined, CodeOutlined, EyeOutlined, DownloadOutlined } from '@ant-design/icons'
import api from '../api/axios'
import dayjs from 'dayjs'
import CodeEditor from '../components/CodeEditor'

const { TabPane } = Tabs;
const { Search } = Input;

const Tasks = () => {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchText, setSearchText] = useState('')
  const [selectedOwnerId, setSelectedOwnerId] = useState<number | undefined>(undefined)  // 筛选的创建者ID
  const [users, setUsers] = useState<any[]>([])  // 用户列表
  const [currentUserRole, setCurrentUserRole] = useState('')  // 当前用户角色
  const [drawerVisible, setDrawerVisible] = useState(false)
  const [viewDrawerVisible, setViewDrawerVisible] = useState(false)
  const [logDrawerVisible, setLogDrawerVisible] = useState(false)
  const [currentTask, setCurrentTask] = useState<any>(null)
  const [currentExecution, setCurrentExecution] = useState<any>(null)
  const [executionLog, setExecutionLog] = useState('')
  const [scriptContent, setScriptContent] = useState('')
  const [scriptMode, setScriptMode] = useState<'write' | 'upload'>('write')
  const [saving, setSaving] = useState(false)
  const [countdowns, setCountdowns] = useState<{[key: number]: number}>({})
  const [logPollingInterval, setLogPollingInterval] = useState<number | null>(null)
  const [logFileRelative, setLogFileRelative] = useState<string | null>(null)
  const [isPartialLog, setIsPartialLog] = useState(false)
  const [loadingFullLog, setLoadingFullLog] = useState(false)
  const [form] = Form.useForm()
  const navigate = useNavigate()

  useEffect(() => {
    fetchCurrentUser()
    fetchUsers()
    fetchTasks()
    
    // 每秒更新倒计时
    const interval = setInterval(() => {
      setCountdowns(prev => {
        const updated = {...prev}
        Object.keys(updated).forEach(key => {
          if (updated[+key] > 0) {
            updated[+key]--
          }
        })
        return updated
      })
    }, 1000)
    
    return () => clearInterval(interval)
  }, [])

  // 日志实时轮询
  useEffect(() => {
    if (logDrawerVisible && currentExecution && currentExecution.status === 'running' && currentTask) {
      // 任务运行中，每2秒刷新一次日志
      const interval = window.setInterval(async () => {
        try {
          const response = await api.get(`/tasks/${currentTask.id}/executions/${currentExecution.id}/log`)
          setExecutionLog(response.data.log || '日志内容为空')
          
          // 同时刷新执行状态
          const executionsRes = await api.get(`/tasks/${currentTask.id}/executions`)
          const updatedExecution = executionsRes.data.find((e: any) => e.id === currentExecution.id)
          if (updatedExecution) {
            setCurrentExecution(updatedExecution)
            // 如果任务已完成，停止轮询
            if (updatedExecution.status !== 'running') {
              clearInterval(interval)
              setLogPollingInterval(null)
            }
          }
        } catch (error) {
          console.error('刷新日志失败', error)
        }
      }, 2000)  // 2秒轮询
      
      setLogPollingInterval(interval)
      
      return () => {
        clearInterval(interval)
        setLogPollingInterval(null)
      }
    } else if (logPollingInterval) {
      // 日志窗口关闭或任务已完成，停止轮询
      clearInterval(logPollingInterval)
      setLogPollingInterval(null)
    }
  }, [logDrawerVisible, currentExecution, currentTask])

  const fetchCurrentUser = async () => {
    try {
      const response = await api.get('/auth/me')
      setCurrentUserRole(response.data.role)
    } catch (error) {
      console.error('获取当前用户信息失败', error)
    }
  }

  const fetchUsers = async () => {
    try {
      const response = await api.get('/users/simple')
      setUsers(response.data)
    } catch (error) {
      console.error('获取用户列表失败', error)
    }
  }

  const fetchTasks = async (search?: string, ownerId?: number) => {
    setLoading(true)
    try {
      const params: any = {}
      if (search) params.search = search
      if (ownerId !== undefined) params.owner_id = ownerId
      
      const response = await api.get('/tasks', { params })
      setTasks(response.data)
      
      // 获取每个任务的下次执行时间
      response.data.forEach(async (task: any) => {
        if (task.is_active) {
          try {
            const countdownRes = await api.get(`/tasks/${task.id}/next-run`)
            if (countdownRes.data.countdown_seconds !== null) {
              setCountdowns(prev => ({
                ...prev,
                [task.id]: countdownRes.data.countdown_seconds
              }))
            }
          } catch (error) {
            // 忽略错误
          }
        }
      })
    } catch (error) {
      message.error('获取任务列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setCurrentTask(null)
    form.resetFields()
    setScriptContent('')
    setScriptMode('write')
    setDrawerVisible(true)
  }

  const handleEdit = async (record: any) => {
    setCurrentTask(record)
    form.setFieldsValue({
      name: record.name,
      description: record.description,
      cron_expression: record.cron_expression,
      script_params: record.script_params || '',  // 回显脚本参数
      is_active: record.is_active
    })
    
    // 加载脚本内容
    if (record.script_path) {
      try {
        const response = await api.get(`/tasks/${record.id}/script`)
        setScriptContent(response.data.content)
        setScriptMode('write')
      } catch (error) {
        message.error('加载脚本内容失败')
        setScriptContent('')
      }
    } else {
      setScriptContent('')
    }
    
    setDrawerVisible(true)
  }

  const handleView = async (record: any) => {
    setCurrentTask(record)
    
    // 加载脚本内容
    if (record.script_path) {
      try {
        const response = await api.get(`/tasks/${record.id}/script`)
        setScriptContent(response.data.content)
        setViewDrawerVisible(true)
      } catch (error) {
        message.error('加载脚本内容失败')
      }
    } else {
      message.warning('该任务还没有脚本')
    }
  }

  const handleSubmit = async (values: any) => {
    // 验证脚本内容
    if (scriptMode === 'write' && !scriptContent.trim()) {
      message.error('请编写脚本内容或上传脚本文件')
      return
    }

    setSaving(true)
    try {
      let taskId = currentTask?.id

      // 1. 创建或更新任务基本信息
      if (currentTask) {
        await api.put(`/tasks/${currentTask.id}`, values)
        message.success('任务更新成功')
      } else {
        const response = await api.post('/tasks', values)
        taskId = response.data.id
        message.success('任务创建成功')
      }

      // 2. 保存脚本内容（新建任务时需要传递 is_active）
      if (scriptMode === 'write' && scriptContent.trim()) {
        const scriptData: any = {
          content: scriptContent
        }
        
        // 如果是新建任务，传递 is_active 状态
        if (!currentTask) {
          scriptData.is_active = values.is_active
        }
        
        await api.post(`/tasks/${taskId}/script`, scriptData)
        message.success('脚本保存成功')
      }

      setDrawerVisible(false)
      fetchTasks()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败')
    } finally {
      setSaving(false)
    }
  }

  const handleUpload = async (options: any) => {
    const { file, onSuccess, onError } = options

    try {
      const reader = new FileReader()
      reader.onload = (e) => {
        const content = e.target?.result as string
        setScriptContent(content)
        setScriptMode('write')
        message.success('文件读取成功，请点击保存')
      }
      reader.readAsText(file)
      onSuccess()
    } catch (error: any) {
      message.error('文件读取失败')
      onError(error)
    }
  }

  const handleDownload = async (task: any) => {
    try {
      const response = await api.get(`/tasks/${task.id}/script/download`, {
        responseType: 'blob'
      })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `task_${task.id}_${task.name}.py`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      message.success('下载成功')
    } catch (error: any) {
      message.error(error.response?.data?.detail || '下载失败')
    }
  }

  const handleSearch = (value: string) => {
    setSearchText(value)
    fetchTasks(value, selectedOwnerId)
  }

  const handleExecute = async (id: number) => {
    // 查找任务信息
    const task = tasks.find(t => t.id === id);
    
    // 检查任务是否启用
    if (task && !task.is_active) {
      message.warning('无法执行，任务是禁用状态');
      return;
    }
    
    try {
      await api.post(`/tasks/${id}/execute`)
      message.success('任务已提交执行')
      fetchTasks()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '执行失败')
    }
  }

  const handleDelete = (id: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个任务吗？',
      onOk: async () => {
        try {
          await api.delete(`/tasks/${id}`)
          message.success('删除成功')
          fetchTasks()
        } catch (error: any) {
          message.error(error.response?.data?.detail || '删除失败')
        }
      }
    })
  }

  const handleToggleActive = async (id: number, isActive: boolean) => {
    try {
      await api.put(`/tasks/${id}`, { is_active: !isActive })
      message.success(isActive ? '已禁用' : '已启用')
      fetchTasks()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败')
    }
  }

  const handleViewLog = async (task: any) => {
    try {
      // 获取最新的执行记录
      const response = await api.get(`/tasks/${task.id}/executions`)
      if (response.data.length === 0) {
        message.warning('该任务还没有执行记录')
        return
      }
      
      const latestExecution = response.data[0]
      setCurrentExecution(latestExecution)
      setCurrentTask(task)
      
      // 获取执行日志（默认部分日志）
      const logResponse = await api.get(`/tasks/${task.id}/executions/${latestExecution.id}/log`)
      setExecutionLog(logResponse.data.log || '日志内容为空')
      setLogFileRelative(logResponse.data.log_file_relative)
      setIsPartialLog(logResponse.data.is_partial)
      setLogDrawerVisible(true)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '获取日志失败')
    }
  }

  const handleLoadFullLog = async () => {
    if (!currentTask || !currentExecution) return
    setLoadingFullLog(true)
    try {
      const response = await api.get(`/tasks/${currentTask.id}/executions/${currentExecution.id}/log`, {
        params: { full: true }
      })
      setExecutionLog(response.data.log || '日志内容为空')
      setIsPartialLog(false)
      message.success('已加载全部日志')
    } catch (error: any) {
      message.error(error.response?.data?.detail || '加载全部日志失败')
    } finally {
      setLoadingFullLog(false)
    }
  }

  const formatCountdown = (seconds: number) => {
    if (seconds === null || seconds === undefined || seconds < 0) {
      return '-'
    }
    
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    
    if (hours > 24) {
      const days = Math.floor(hours / 24)
      return `${days}天`
    } else if (hours > 0) {
      return `${hours}时${minutes}分`
    } else if (minutes > 0) {
      return `${minutes}分${secs}秒`
    } else {
      return `${secs}秒`
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
    { title: '任务名称', dataIndex: 'name', key: 'name', width: 120 },
    { 
      title: '创建者', 
      dataIndex: 'owner_username', 
      key: 'owner_username',
      width: 100,
      render: (username: string) => username || '-'
    },
    { title: 'Cron表达式', dataIndex: 'cron_expression', key: 'cron_expression', width: 120 },
    { 
      title: '状态', 
      dataIndex: 'status', 
      key: 'status',
      width: 80,
      render: (status: string) => (
        <Tag color={statusColors[status]}>{statusText[status] || status}</Tag>
      )
    },
    { 
      title: '是否启用', 
      dataIndex: 'is_active', 
      key: 'is_active',
      render: (active: boolean, record: any) => (
        <AntSwitch
          checked={active}
          onChange={() => handleToggleActive(record.id, active)}
          checkedChildren="启用"
          unCheckedChildren="禁用"
        />
      )
    },
    { 
      title: '脚本状态',
      dataIndex: 'script_path',
      key: 'script_path',
      render: (path: string) => (
        <Tag color={path ? 'success' : 'warning'}>
          {path ? '已上传' : '未上传'}
        </Tag>
      )
    },
    { 
      title: '最后运行', 
      dataIndex: 'last_run_at', 
      key: 'last_run_at',
      render: (time: string) => time ? dayjs(time).format('YYYY-MM-DD HH:mm:ss') : '-'
    },
    {
      title: '下次执行',
      key: 'next_run',
      render: (_: any, record: any) => {
        if (!record.is_active) {
          return <Tag>未启用</Tag>
        }
        const countdown = countdowns[record.id]
        if (countdown === undefined || countdown === null) {
          return <Tag color="default">计算中...</Tag>
        }
        if (countdown <= 0) {
          return <Tag color="processing">即将执行</Tag>
        }
        return <Tag color="blue">{formatCountdown(countdown)}</Tag>
      }
    },
    {
      title: '操作',
      key: 'action',
      width: 400,
      render: (_: any, record: any) => (
        <Space size="small">
          <Button 
            type="link" 
            size="small"
            icon={<PlayCircleOutlined />}
            onClick={() => handleExecute(record.id)}
            disabled={!record.script_path}
          >
            执行
          </Button>
          <Button 
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleView(record)}
            disabled={!record.script_path}
          >
            查看脚本
          </Button>
          <Button 
            type="link" 
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Button 
            type="link" 
            size="small"
            icon={<DownloadOutlined />}
            onClick={() => handleDownload(record)}
            disabled={!record.script_path}
          >
            下载
          </Button>
          <Button 
            type="link" 
            size="small"
            onClick={() => handleViewLog(record)}
            disabled={!record.script_path}
          >
            查看日志
          </Button>
          <Button 
            type="link" 
            size="small"
            onClick={() => navigate(`/tasks/${record.id}`)}
          >
            详情
          </Button>
          <Button 
            type="link" 
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          创建任务
        </Button>
        
        <Space>
          {/* 仅管理员显示创建者筛选 */}
          {currentUserRole === 'admin' && (
            <Select
              placeholder="筛选创建者"
              allowClear
              style={{ width: 150 }}
              value={selectedOwnerId}
              onChange={(value) => {
                setSelectedOwnerId(value)
                fetchTasks(searchText, value)
              }}
            >
              {users.map(user => (
                <Select.Option key={user.id} value={user.id}>
                  {user.username}
                </Select.Option>
              ))}
            </Select>
          )}
          
          <Search
            placeholder="搜索任务名、描述或Cron表达式"
            allowClear
            enterButton="搜索"
            style={{ width: 400 }}
            onSearch={handleSearch}
          />
        </Space>
      </div>

      <Table
        dataSource={tasks}
        columns={columns}
        rowKey="id"
        loading={loading}
      />

      {/* 创建/编辑任务Drawer */}
      <Drawer
        title={currentTask ? '编辑任务' : '创建任务'}
        width={900}
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
        footer={
          <div style={{ textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setDrawerVisible(false)}>取消</Button>
              <Button type="primary" loading={saving} onClick={() => form.submit()}>
                保存
              </Button>
            </Space>
          </div>
        }
      >
        <Form form={form} onFinish={handleSubmit} layout="vertical">
          <Form.Item
            name="name"
            label="任务名称"
            rules={[{ required: true, message: '请输入任务名称' }]}
          >
            <Input placeholder="例如：每日数据备份" />
          </Form.Item>
          
          <Form.Item name="description" label="任务描述">
            <Input.TextArea rows={2} placeholder="描述任务的功能和目的" />
          </Form.Item>
          
          <Form.Item
            name="cron_expression"
            label="Cron表达式"
            rules={[{ required: true, message: '请输入Cron表达式' }]}
            extra="例如: 0 0 * * * (每天0点执行), */5 * * * * (每5分钟执行)"
          >
            <Input placeholder="0 0 * * *" />
          </Form.Item>

          <Form.Item
            name="script_params"
            label="脚本参数（可选）"
            extra="命令行参数，例如: --file data.txt --mode prod"
          >
            <Input placeholder="--file input.txt --limit 100" />
          </Form.Item>

          <Form.Item
            name="is_active"
            label="是否启用"
            valuePropName="checked"
            initialValue={false}
          >
            <AntSwitch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>
        </Form>

        <div style={{ marginTop: 24 }}>
          <Tabs activeKey={scriptMode} onChange={(key) => setScriptMode(key as any)}>
            <TabPane tab={<span><CodeOutlined /> 编写脚本</span>} key="write">
              <div style={{ marginBottom: 8 }}>
                <Space>
                  <Button
                    size="small"
                    icon={<UploadOutlined />}
                    onClick={() => {
                      const input = document.createElement('input')
                      input.type = 'file'
                      input.accept = '.py'
                      input.onchange = (e: any) => {
                        const file = e.target.files[0]
                        if (file) {
                          handleUpload({ file, onSuccess: () => {}, onError: () => {} })
                        }
                      }
                      input.click()
                    }}
                  >
                    从文件导入
                  </Button>
                  <span style={{ color: '#999', fontSize: 12 }}>
                    支持 .py 文件
                  </span>
                </Space>
              </div>
              <CodeEditor
                value={scriptContent}
                onChange={setScriptContent}
                language="python"
                height="400px"
              />
              {scriptContent.trim() && (
                <div style={{ marginTop: 8, color: '#52c41a', fontSize: 12 }}>
                  ✓ 脚本已就绪，共 {scriptContent.split('\n').length} 行
                </div>
              )}
            </TabPane>
            
            <TabPane tab={<span><UploadOutlined /> 上传文件</span>} key="upload">
              <Upload.Dragger
                name="file"
                accept=".py"
                customRequest={handleUpload}
                maxCount={1}
                showUploadList={false}
              >
                <p className="ant-upload-drag-icon">
                  <UploadOutlined style={{ fontSize: 48 }} />
                </p>
                <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
                <p className="ant-upload-hint">
                  仅支持 .py 文件，上传后可以在"编写脚本"标签中查看和编辑
                </p>
              </Upload.Dragger>
            </TabPane>
          </Tabs>
        </div>
      </Drawer>

      {/* 查看脚本Drawer */}
      <Drawer
        title={`查看脚本 - ${currentTask?.name || ''}`}
        width={800}
        open={viewDrawerVisible}
        onClose={() => setViewDrawerVisible(false)}
        footer={
          <div style={{ textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setViewDrawerVisible(false)}>关闭</Button>
              <Button 
                type="primary" 
                icon={<EditOutlined />}
                onClick={() => {
                  setViewDrawerVisible(false)
                  handleEdit(currentTask)
                }}
              >
                编辑脚本
              </Button>
            </Space>
          </div>
        }
      >
        <CodeEditor
          value={scriptContent}
          onChange={() => {}} // readOnly模式下不需要实际修改
          language="python"
          height="600px"
          readOnly
        />
      </Drawer>

      {/* 查看日志Drawer */}
      <Drawer
        title={`执行日志 - ${currentTask?.name || ''}`}
        width={900}
        open={logDrawerVisible}
        onClose={() => setLogDrawerVisible(false)}
        footer={
          <div style={{ textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setLogDrawerVisible(false)}>关闭</Button>
              {isPartialLog && (
                <Button 
                  type="primary"
                  loading={loadingFullLog}
                  onClick={handleLoadFullLog}
                >
                  查看全部日志
                </Button>
              )}
              <Button 
                type="primary" 
                onClick={() => navigate(`/tasks/${currentTask?.id}`)}
              >
                查看所有执行记录
              </Button>
            </Space>
          </div>
        }
      >
        {currentExecution && (
          <div style={{ marginBottom: 16 }}>
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <div><strong>执行ID:</strong> {currentExecution.id}</div>
              <div><strong>触发方式:</strong> <Tag>{currentExecution.trigger_type === 'manual' ? '手动执行' : '定时执行'}</Tag></div>
              <div><strong>状态:</strong> <Tag color={statusColors[currentExecution.status]}>{statusText[currentExecution.status]}</Tag></div>
              <div><strong>开始时间:</strong> {dayjs(currentExecution.start_time).format('YYYY-MM-DD HH:mm:ss')}</div>
              {currentExecution.end_time && (
                <div><strong>结束时间:</strong> {dayjs(currentExecution.end_time).format('YYYY-MM-DD HH:mm:ss')}</div>
              )}
              {logFileRelative && (
                <div><strong>日志文件:</strong> <code style={{ background: '#f0f0f0', padding: '2px 6px', borderRadius: '3px' }}>{logFileRelative}</code></div>
              )}
            </Space>
          </div>
        )}
        {isPartialLog && (
          <Alert
            message="当前仅显示最后100行日志"
            description="如需查看完整日志，请点击下方查看全部日志按钮"
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}
        <div style={{ 
          background: '#1e1e1e', 
          color: '#d4d4d4', 
          padding: '16px', 
          borderRadius: '4px',
          fontFamily: 'Consolas, Monaco, monospace',
          fontSize: '12px',
          maxHeight: '600px',
          overflow: 'auto',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word'
        }}>
          {executionLog || '暂无日志内容'}
        </div>
      </Drawer>
    </div>
  )
}

export default Tasks
