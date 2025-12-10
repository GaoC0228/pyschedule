import { useState } from 'react'
import { Card, Descriptions, Button, Modal, Form, Input, message } from 'antd'
import { UserOutlined, MailOutlined, LockOutlined, TagOutlined } from '@ant-design/icons'
import { useAuth } from '../contexts/AuthContext'
import api from '../api/axios'

const Profile = () => {
  const { user } = useAuth()
  const [passwordModalVisible, setPasswordModalVisible] = useState(false)
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()

  const handleChangePassword = async (values: any) => {
    setLoading(true)
    try {
      await api.put('/auth/change-password', {
        old_password: values.oldPassword,
        new_password: values.newPassword
      })
      message.success('密码修改成功！')
      setPasswordModalVisible(false)
      form.resetFields()
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || '密码修改失败'
      message.error(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <Card title="个人信息" style={{ marginBottom: 24 }}>
        <Descriptions column={1} bordered>
          <Descriptions.Item label={<><UserOutlined /> 用户名</>}>
            {user?.username}
          </Descriptions.Item>
          <Descriptions.Item label={<><MailOutlined /> 邮箱</>}>
            {user?.email || '未设置'}
          </Descriptions.Item>
          <Descriptions.Item label={<><TagOutlined /> 角色</>}>
            {user?.role === 'admin' ? '管理员' : '普通用户'}
          </Descriptions.Item>
          <Descriptions.Item label="账号状态">
            {user?.is_active ? (
              <span style={{ color: '#52c41a' }}>✓ 正常</span>
            ) : (
              <span style={{ color: '#ff4d4f' }}>✗ 已禁用</span>
            )}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="安全设置">
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 14, color: '#666', marginBottom: 8 }}>
            <LockOutlined /> 登录密码
          </div>
          <div style={{ color: '#999', fontSize: 13, marginBottom: 12 }}>
            定期修改密码可以提高账号安全性
          </div>
          <Button type="primary" onClick={() => setPasswordModalVisible(true)}>
            修改密码
          </Button>
        </div>
      </Card>

      <Modal
        title="修改密码"
        open={passwordModalVisible}
        onCancel={() => {
          setPasswordModalVisible(false)
          form.resetFields()
        }}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleChangePassword}
        >
          <Form.Item
            label="当前密码"
            name="oldPassword"
            rules={[{ required: true, message: '请输入当前密码' }]}
          >
            <Input.Password placeholder="请输入当前密码" />
          </Form.Item>

          <Form.Item
            label="新密码"
            name="newPassword"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 6, message: '密码至少6个字符' }
            ]}
          >
            <Input.Password placeholder="请输入新密码（至少6个字符）" />
          </Form.Item>

          <Form.Item
            label="确认新密码"
            name="confirmPassword"
            dependencies={['newPassword']}
            rules={[
              { required: true, message: '请确认新密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('newPassword') === value) {
                    return Promise.resolve()
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'))
                }
              })
            ]}
          >
            <Input.Password placeholder="请再次输入新密码" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <Button type="primary" htmlType="submit" loading={loading} block>
              确认修改
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Profile
