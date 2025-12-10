import React, { useEffect, useState } from 'react'
import { 
  Table, Tag, message, Button, Space, Input, Modal, Form, 
  Select, Switch, Popconfirm, Card
} from 'antd'
import { 
  PlusOutlined, EditOutlined, DeleteOutlined, KeyOutlined,
  SearchOutlined, UserOutlined, MailOutlined, LockOutlined,
  CheckCircleOutlined, StopOutlined
} from '@ant-design/icons'
import api from '../api/axios'
import dayjs from 'dayjs'

interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
  is_online: boolean;  // 在线状态
  last_activity: string | null;  // 最后活动时间
  created_at: string;
  updated_at: string;
}

const Users = () => {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [searchKeyword, setSearchKeyword] = useState('')
  const [modalVisible, setModalVisible] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [passwordModalVisible, setPasswordModalVisible] = useState(false)
  const [resetUserId, setResetUserId] = useState<number | null>(null)
  const [form] = Form.useForm()
  const [passwordForm] = Form.useForm()

  useEffect(() => {
    fetchUsers()
  }, [])

  const fetchUsers = async () => {
    setLoading(true)
    try {
      const params = searchKeyword ? { search: searchKeyword } : {}
      const response = await api.get('/users', { params })
      setUsers(response.data)
    } catch (error: any) {
      message.error('获取用户列表失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  // 搜索
  const handleSearch = () => {
    fetchUsers()
  }

  // 打开新建/编辑对话框
  const handleOpenModal = (user?: User) => {
    if (user) {
      setEditingUser(user)
      form.setFieldsValue({
        username: user.username,
        email: user.email,
        role: user.role,
        is_active: user.is_active
      })
    } else {
      setEditingUser(null)
      form.resetFields()
      form.setFieldsValue({ role: 'user', is_active: true })
    }
    setModalVisible(true)
  }

  // 保存用户
  const handleSave = async () => {
    try {
      const values = await form.validateFields()
      
      if (editingUser) {
        // 更新用户
        await api.put(`/users/${editingUser.id}`, values)
        message.success('用户更新成功')
      } else {
        // 创建用户
        await api.post('/users', values)
        message.success('用户创建成功')
      }
      
      setModalVisible(false)
      form.resetFields()
      fetchUsers()
    } catch (error: any) {
      if (error.response?.data?.detail) {
        message.error(error.response.data.detail)
      } else if (error.errorFields) {
        message.error('请填写必填字段')
      } else {
        message.error('操作失败')
      }
    }
  }

  // 删除用户
  const handleDelete = async (userId: number) => {
    try {
      await api.delete(`/users/${userId}`)
      message.success('用户删除成功')
      fetchUsers()
    } catch (error: any) {
      message.error('删除失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  // 打开重置密码对话框
  const handleOpenPasswordModal = (userId: number) => {
    setResetUserId(userId)
    passwordForm.resetFields()
    setPasswordModalVisible(true)
  }

  // 重置密码
  const handleResetPassword = async () => {
    try {
      const values = await passwordForm.validateFields()
      await api.post(`/users/${resetUserId}/reset-password`, null, {
        params: { new_password: values.new_password }
      })
      message.success('密码重置成功')
      setPasswordModalVisible(false)
      passwordForm.resetFields()
    } catch (error: any) {
      message.error('重置密码失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  // 切换用户状态
  const handleToggleStatus = async (userId: number) => {
    try {
      const response = await api.post(`/users/${userId}/toggle-status`)
      message.success(response.data.message)
      fetchUsers()
    } catch (error: any) {
      message.error('操作失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const columns = [
    { 
      title: 'ID', 
      dataIndex: 'id', 
      key: 'id',
      width: 80
    },
    { 
      title: '用户名', 
      dataIndex: 'username', 
      key: 'username',
      render: (text: string) => (
        <Space>
          <UserOutlined />
          <span>{text}</span>
        </Space>
      )
    },
    { 
      title: '邮箱', 
      dataIndex: 'email', 
      key: 'email',
      render: (text: string) => (
        <Space>
          <MailOutlined />
          <span>{text}</span>
        </Space>
      )
    },
    { 
      title: '角色', 
      dataIndex: 'role', 
      key: 'role',
      width: 100,
      render: (role: string) => (
        <Tag color={role === 'admin' ? 'red' : 'blue'}>
          {role === 'admin' ? '管理员' : '普通用户'}
        </Tag>
      )
    },
    { 
      title: '在线状态', 
      dataIndex: 'is_online', 
      key: 'is_online',
      width: 100,
      render: (isOnline: boolean) => (
        <Tag icon={isOnline ? <CheckCircleOutlined /> : <StopOutlined />} color={isOnline ? 'success' : 'default'}>
          {isOnline ? '在线' : '离线'}
        </Tag>
      )
    },
    { 
      title: '创建时间', 
      dataIndex: 'created_at', 
      key: 'created_at',
      width: 180,
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm:ss')
    },
    {
      title: '操作',
      key: 'action',
      width: 280,
      render: (_: any, record: User) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleOpenModal(record)}
          >
            编辑
          </Button>
          <Button
            type="link"
            size="small"
            icon={<KeyOutlined />}
            onClick={() => handleOpenPasswordModal(record.id)}
          >
            重置密码
          </Button>
          <Popconfirm
            title={`确定${record.is_active ? '禁用' : '启用'}此用户吗？`}
            onConfirm={() => handleToggleStatus(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              size="small"
              icon={record.is_active ? <StopOutlined /> : <CheckCircleOutlined />}
            >
              {record.is_active ? '禁用' : '启用'}
            </Button>
          </Popconfirm>
          <Popconfirm
            title="确定删除此用户吗？此操作不可恢复！"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            okType="danger"
            cancelText="取消"
          >
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ]

  return (
    <div>
      <Card>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* 顶部操作栏 */}
          <Space style={{ width: '100%', justifyContent: 'space-between' }}>
            <Space>
              <Input.Search
                placeholder="搜索用户名或邮箱"
                allowClear
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                onSearch={handleSearch}
                style={{ width: 300 }}
                prefix={<SearchOutlined />}
              />
              <Button onClick={handleSearch}>搜索</Button>
            </Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => handleOpenModal()}
            >
              新建用户
            </Button>
          </Space>

          {/* 用户列表 */}
          <Table
            dataSource={users}
            columns={columns}
            rowKey="id"
            loading={loading}
            pagination={{
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `共 ${total} 条记录`
            }}
          />
        </Space>
      </Card>

      {/* 新建/编辑用户对话框 */}
      <Modal
        title={editingUser ? '编辑用户' : '新建用户'}
        open={modalVisible}
        onOk={handleSave}
        onCancel={() => {
          setModalVisible(false)
          form.resetFields()
        }}
        width={600}
        okText="保存"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          autoComplete="off"
        >
          <Form.Item
            label="用户名"
            name="username"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 3, message: '用户名至少3个字符' },
              { max: 50, message: '用户名最多50个字符' },
              { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线' }
            ]}
          >
            <Input 
              prefix={<UserOutlined />} 
              placeholder="请输入用户名" 
              disabled={!!editingUser}
            />
          </Form.Item>

          <Form.Item
            label="邮箱"
            name="email"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' }
            ]}
          >
            <Input prefix={<MailOutlined />} placeholder="请输入邮箱" />
          </Form.Item>

          {!editingUser && (
            <Form.Item
              label="密码"
              name="password"
              rules={[
                { required: true, message: '请输入密码' },
                { min: 6, message: '密码至少6个字符' },
                { max: 50, message: '密码最多50个字符' }
              ]}
            >
              <Input.Password 
                prefix={<LockOutlined />} 
                placeholder="请输入密码（至少6位）" 
              />
            </Form.Item>
          )}

          <Form.Item
            label="角色"
            name="role"
            rules={[{ required: true, message: '请选择角色' }]}
          >
            <Select>
              <Select.Option value="user">普通用户</Select.Option>
              <Select.Option value="admin">管理员</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="状态"
            name="is_active"
            valuePropName="checked"
          >
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 重置密码对话框 */}
      <Modal
        title="重置密码"
        open={passwordModalVisible}
        onOk={handleResetPassword}
        onCancel={() => {
          setPasswordModalVisible(false)
          passwordForm.resetFields()
        }}
        okText="确定"
        cancelText="取消"
      >
        <Form
          form={passwordForm}
          layout="vertical"
        >
          <Form.Item
            label="新密码"
            name="new_password"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 6, message: '密码至少6个字符' },
              { max: 50, message: '密码最多50个字符' }
            ]}
          >
            <Input.Password 
              prefix={<LockOutlined />} 
              placeholder="请输入新密码（至少6位）" 
            />
          </Form.Item>
          <Form.Item
            label="确认密码"
            name="confirm_password"
            dependencies={['new_password']}
            rules={[
              { required: true, message: '请确认新密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('new_password') === value) {
                    return Promise.resolve()
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'))
                },
              }),
            ]}
          >
            <Input.Password 
              prefix={<LockOutlined />} 
              placeholder="请再次输入新密码" 
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Users
