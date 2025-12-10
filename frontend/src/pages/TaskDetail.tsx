import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Descriptions, Table, Tag, Button, Space, Modal, message, Input, Alert } from 'antd'
import { ArrowLeftOutlined, EyeOutlined, DownloadOutlined, FileOutlined } from '@ant-design/icons'
import api from '../api/axios'
import dayjs from 'dayjs'

const { Search } = Input;

const TaskDetail = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const [task, setTask] = useState<any>(null)
  const [executions, setExecutions] = useState([])
  const [loading, setLoading] = useState(true)
  const [logModalVisible, setLogModalVisible] = useState(false)
  const [filesModalVisible, setFilesModalVisible] = useState(false)
  const [currentLog, setCurrentLog] = useState('')
  const [currentExecution, setCurrentExecution] = useState<any>(null)
  const [outputFiles, setOutputFiles] = useState<any[]>([])
  const [searchKeyword, setSearchKeyword] = useState('')
  const [searchResults, setSearchResults] = useState<any>(null)
  const [searching, setSearching] = useState(false)

  useEffect(() => {
    fetchData()
  }, [id])

  const fetchData = async () => {
    try {
      const [taskRes, executionsRes] = await Promise.all([
        api.get(`/tasks/${id}`),
        api.get(`/tasks/${id}/executions`)
      ])
      setTask(taskRes.data)
      setExecutions(executionsRes.data)
    } catch (error) {
      console.error('获取任务详情失败', error)
    } finally {
      setLoading(false)
    }
  }

  const handleViewLog = async (execution: any) => {
    try {
      const response = await api.get(`/tasks/${id}/executions/${execution.id}/log`)
      setCurrentLog(response.data.log || '日志内容为空')
      setCurrentExecution(execution)
      setLogModalVisible(true)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '获取日志失败')
    }
  }

  const handleSearchLogs = async (keyword: string) => {
    if (!keyword.trim()) {
      message.warning('请输入搜索关键字')
      return
    }
    
    setSearching(true)
    setSearchKeyword(keyword)
    try {
      const response = await api.get(`/tasks/${id}/executions/search`, {
        params: { keyword }
      })
      setSearchResults(response.data)
      if (response.data.total === 0) {
        message.info('未找到包含该关键字的执行记录')
      } else {
        message.success(`找到 ${response.data.total} 条匹配的执行记录`)
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '搜索失败')
    } finally {
      setSearching(false)
    }
  }

  const handleViewFiles = async (execution: any) => {
    try {
      const response = await api.get(`/tasks/${id}/executions/${execution.id}/files`)
      setOutputFiles(response.data.files || [])
      setCurrentExecution(execution)
      setFilesModalVisible(true)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '获取文件列表失败')
    }
  }

  const handleDownloadFile = async (filename: string) => {
    if (!currentExecution) return
    try {
      const response = await api.get(
        `/tasks/${id}/executions/${currentExecution.id}/files/${encodeURIComponent(filename)}`,
        { responseType: 'blob' }
      )
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      message.success('下载成功')
    } catch (error: any) {
      message.error(error.response?.data?.detail || '下载失败')
    }
  }

  const handlePreviewFile = async (filename: string) => {
    if (!currentExecution) return
    
    // 判断是否为可预览的文本文件
    const textExtensions = ['.txt', '.log', '.json', '.csv', '.xml', '.md', '.py', '.js', '.html', '.css', '.sql']
    const isTextFile = textExtensions.some(ext => filename.toLowerCase().endsWith(ext))
    
    if (!isTextFile) {
      message.warning('仅支持预览文本文件')
      return
    }
    
    try {
      const response = await api.get(
        `/tasks/${id}/executions/${currentExecution.id}/preview-file/${encodeURIComponent(filename)}`
      )
      
      Modal.info({
        title: `文件预览 - ${filename}`,
        width: 900,
        content: (
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
            {response.data.content}
          </div>
        )
      })
    } catch (error: any) {
      message.error(error.response?.data?.detail || '预览失败')
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
    return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
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
    { 
      title: '执行ID', 
      dataIndex: 'id', 
      key: 'id',
      width: 80,
      render: (id: number) => `#${id}`
    },
    { 
      title: '状态', 
      dataIndex: 'status', 
      key: 'status',
      render: (status: string) => (
        <Tag color={statusColors[status]}>{statusText[status]}</Tag>
      )
    },
    {
      title: '触发方式',
      dataIndex: 'trigger_type',
      key: 'trigger_type',
      render: (type: string) => (
        <Tag>{type === 'manual' ? '手动执行' : '定时执行'}</Tag>
      )
    },
    { 
      title: '开始时间', 
      dataIndex: 'start_time', 
      key: 'start_time',
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm:ss')
    },
    { 
      title: '结束时间', 
      dataIndex: 'end_time', 
      key: 'end_time',
      render: (time: string) => time ? dayjs(time).format('YYYY-MM-DD HH:mm:ss') : '-'
    },
    {
      title: '执行时长',
      key: 'duration',
      render: (_: any, record: any) => {
        if (!record.end_time) return '-'
        const duration = dayjs(record.end_time).diff(dayjs(record.start_time), 'second')
        return duration >= 60 ? `${Math.floor(duration / 60)}分${duration % 60}秒` : `${duration}秒`
      }
    },
    {
      title: '退出码',
      dataIndex: 'exit_code',
      key: 'exit_code',
      render: (code: number) => {
        if (code === null || code === undefined) return '-'
        return <Tag color={code === 0 ? 'success' : 'error'}>{code}</Tag>
      }
    },
    {
      title: '产出文件',
      key: 'output_files',
      render: (_: any, record: any) => {
        const files = record.output_files ? JSON.parse(record.output_files) : []
        if (files.length === 0) {
          return <Tag>无</Tag>
        }
        return (
          <Space>
            <Tag color="success" icon={<FileOutlined />}>{files.length} 个</Tag>
            <Button type="link" size="small" onClick={() => handleViewFiles(record)}>
              查看
            </Button>
          </Space>
        )
      }
    },
    { 
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Button 
          type="link" 
          size="small"
          icon={<EyeOutlined />}
          onClick={() => handleViewLog(record)}
        >
          查看日志
        </Button>
      )
    },
  ]

  if (loading || !task) {
    return <Card loading={loading} />
  }

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/tasks')}>
          返回
        </Button>
      </Space>

      <Card title="任务详情" style={{ marginBottom: 16 }}>
        <Descriptions column={2}>
          <Descriptions.Item label="任务名称">{task.name}</Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={statusColors[task.status]}>{statusText[task.status]}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Cron表达式">{task.cron_expression}</Descriptions.Item>
          <Descriptions.Item label="脚本参数">
            {task.script_params ? (
              <code style={{background: '#f5f5f5', padding: '2px 6px', borderRadius: '3px'}}>
                {task.script_params}
              </code>
            ) : '无'}
          </Descriptions.Item>
          <Descriptions.Item label="是否启用">
            <Tag color={task.is_active ? 'success' : 'default'}>
              {task.is_active ? '启用' : '禁用'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="脚本路径">{task.script_path || '未上传'}</Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {dayjs(task.created_at).format('YYYY-MM-DD HH:mm:ss')}
          </Descriptions.Item>
          <Descriptions.Item label="最后运行">
            {task.last_run_at ? dayjs(task.last_run_at).format('YYYY-MM-DD HH:mm:ss') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="下次运行">
            {task.next_run_at ? dayjs(task.next_run_at).format('YYYY-MM-DD HH:mm:ss') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="创建者">{task.owner_username || '-'}</Descriptions.Item>
          <Descriptions.Item label="描述" span={2}>{task.description || '-'}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="执行记录" style={{ marginBottom: 16 }}>
        <div style={{ marginBottom: 16 }}>
          <Search
            placeholder="搜索日志关键字（如错误信息、特定输出等）"
            enterButton="搜索日志"
            size="large"
            onSearch={handleSearchLogs}
            loading={searching}
            allowClear
          />
        </div>

        {searchResults && searchResults.total > 0 && (
          <Alert
            message={`搜索结果：找到 ${searchResults.total} 条包含"${searchKeyword}"的执行记录`}
            type="success"
            closable
            style={{ marginBottom: 16 }}
            onClose={() => setSearchResults(null)}
          />
        )}

        {searchResults && searchResults.total > 0 && (
          <Card size="small" title={`匹配的执行记录（${searchResults.total}条）`} style={{ marginBottom: 16 }}>
            {searchResults.executions.map((exec: any) => (
              <div key={exec.id} style={{ marginBottom: 12, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  <div>
                    <strong>执行ID: #{exec.id}</strong>
                    {' | '}
                    <Tag color={statusColors[exec.status]}>{statusText[exec.status]}</Tag>
                    {' | '}
                    <Tag>{exec.trigger_type === 'manual' ? '手动执行' : '定时执行'}</Tag>
                    {' | '}
                    时间: {dayjs(exec.start_time).format('YYYY-MM-DD HH:mm:ss')}
                    {exec.exit_code !== null && exec.exit_code !== undefined && (
                      <> | 退出码: <Tag color={exec.exit_code === 0 ? 'success' : 'error'}>{exec.exit_code}</Tag></>
                    )}
                  </div>
                  <div style={{ background: '#1e1e1e', color: '#d4d4d4', padding: 8, borderRadius: 4, fontSize: 12, fontFamily: 'monospace' }}>
                    <div style={{ color: '#4caf50', marginBottom: 4 }}>匹配的日志行：</div>
                    {exec.matched_lines.map((line: string, idx: number) => (
                      <div key={idx}>{line}</div>
                    ))}
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <Button size="small" type="link" onClick={() => handleViewLog(exec)}>
                      查看完整日志
                    </Button>
                  </div>
                </Space>
              </div>
            ))}
          </Card>
        )}

        <Table
          dataSource={executions}
          columns={columns}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {/* 查看日志Modal */}
      <Modal
        title={`执行日志 - ${currentExecution ? `#${currentExecution.id}` : ''}`}
        open={logModalVisible}
        onCancel={() => setLogModalVisible(false)}
        width={900}
        footer={[
          <Button key="close" onClick={() => setLogModalVisible(false)}>
            关闭
          </Button>
        ]}
      >
        {currentExecution && (
          <div style={{ marginBottom: 16 }}>
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <div><strong>执行ID:</strong> {currentExecution.id}</div>
              <div><strong>触发方式:</strong> <Tag>{currentExecution.trigger_type === 'manual' ? '手动执行' : '定时执行'}</Tag></div>
              <div><strong>状态:</strong> <Tag color={statusColors[currentExecution.status]}>{statusText[currentExecution.status]}</Tag></div>
              <div><strong>开始时间:</strong> {dayjs(currentExecution.start_time).format('YYYY-MM-DD HH:mm:ss')}</div>
              {currentExecution.end_time && (
                <>
                  <div><strong>结束时间:</strong> {dayjs(currentExecution.end_time).format('YYYY-MM-DD HH:mm:ss')}</div>
                  <div><strong>执行时长:</strong> {dayjs(currentExecution.end_time).diff(dayjs(currentExecution.start_time), 'second')}秒</div>
                </>
              )}
              {currentExecution.exit_code !== null && currentExecution.exit_code !== undefined && (
                <div><strong>退出码:</strong> <Tag color={currentExecution.exit_code === 0 ? 'success' : 'error'}>{currentExecution.exit_code}</Tag></div>
              )}
            </Space>
          </div>
        )}
        <div style={{ 
          background: '#1e1e1e', 
          color: '#d4d4d4', 
          padding: '16px', 
          borderRadius: '4px',
          fontFamily: 'Consolas, Monaco, monospace',
          fontSize: '12px',
          maxHeight: '500px',
          overflow: 'auto',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word'
        }}>
          {currentLog || '暂无日志内容'}
        </div>
      </Modal>

      {/* 产出文件Modal */}
      <Modal
        title={`产出文件 - ${currentExecution ? `#${currentExecution.id}` : ''}`}
        open={filesModalVisible}
        onCancel={() => setFilesModalVisible(false)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setFilesModalVisible(false)}>
            关闭
          </Button>
        ]}
      >
        {outputFiles.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
            <FileOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
            <div>此次执行未产出任何文件</div>
          </div>
        ) : (
          <Table
            dataSource={outputFiles}
            rowKey="name"
            pagination={false}
            size="small"
            onRow={(record) => ({
              onDoubleClick: () => handlePreviewFile(record.name),
              style: { cursor: 'pointer' }
            })}
            columns={[
              {
                title: '文件名（双击预览）',
                dataIndex: 'name',
                key: 'name',
                render: (name: string) => (
                  <Space>
                    <FileOutlined />
                    <span style={{ color: '#1890ff' }}>{name}</span>
                  </Space>
                )
              },
              {
                title: '大小',
                dataIndex: 'size',
                key: 'size',
                width: 120,
                render: (size: number) => formatFileSize(size)
              },
              {
                title: '生成时间',
                dataIndex: 'created_at',
                key: 'created_at',
                width: 180
              },
              {
                title: '操作',
                key: 'action',
                width: 150,
                render: (_: any, file: any) => (
                  <Space>
                    <Button
                      type="link"
                      size="small"
                      icon={<EyeOutlined />}
                      onClick={() => handlePreviewFile(file.name)}
                    >
                      预览
                    </Button>
                    <Button
                      type="link"
                      size="small"
                      icon={<DownloadOutlined />}
                      onClick={() => handleDownloadFile(file.name)}
                    >
                      下载
                    </Button>
                  </Space>
                )
              }
            ]}
          />
        )}
      </Modal>
    </div>
  )
}

export default TaskDetail
