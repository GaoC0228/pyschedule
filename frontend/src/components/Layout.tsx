import { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout as AntLayout, Menu, Avatar, Dropdown, Space } from 'antd'
import {
  DashboardOutlined,
  ClockCircleOutlined,
  UserOutlined,
  AuditOutlined,
  LogoutOutlined,
  SettingOutlined,
  CodeOutlined,
  DatabaseOutlined,
  DeleteOutlined,
  CodepenOutlined,
  AppstoreAddOutlined,
} from '@ant-design/icons'
import { useAuth } from '../contexts/AuthContext'

const { Header, Sider, Content } = AntLayout

const Layout = () => {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuth()

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表盘',
    },
    {
      key: '/tasks',
      icon: <ClockCircleOutlined />,
      label: '任务管理',
    },
    {
      key: '/workspace',
      icon: <CodeOutlined />,
      label: '工作区',
    },
    {
      key: '/database-config',
      icon: <DatabaseOutlined />,
      label: '数据库配置',
    },
    ...(user?.role === 'admin' || user?.can_manage_packages ? [{
      key: '/packages',
      icon: <AppstoreAddOutlined />,
      label: '包管理',
    }] : []),
    ...(user?.role === 'admin' ? [{
      key: '/users',
      icon: <UserOutlined />,
      label: '用户管理',
    }] : []),
    ...(user?.role === 'admin' ? [{
      key: '/audit',
      icon: <AuditOutlined />,
      label: '审计日志',
    }] : []),
    ...(user?.role === 'admin' ? [{
      key: '/audit-cleaner',
      icon: <DeleteOutlined />,
      label: '日志清理',
    }] : []),
    ...(user?.role === 'admin' ? [{
      key: '/web-terminal',
      icon: <CodepenOutlined />,
      label: 'Web终端',
    }] : []),
  ]

  const userMenuItems = [
    {
      key: 'profile',
      icon: <SettingOutlined />,
      label: '个人设置',
      onClick: () => {
        navigate('/profile')
      },
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: () => {
        logout()
        navigate('/login')
      },
    },
  ]

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed}>
        <div style={{ 
          height: 64, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          color: 'white',
          fontSize: collapsed ? 16 : 18,
          fontWeight: 'bold'
        }}>
          {collapsed ? 'PT' : 'Python任务平台'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <AntLayout>
        <Header style={{ 
          padding: '0 24px', 
          background: '#fff',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div style={{ fontSize: 20, fontWeight: 500 }}>
            {menuItems.find(item => item.key === location.pathname)?.label || ''}
          </div>
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Space style={{ cursor: 'pointer' }}>
              <Avatar icon={<UserOutlined />} />
              <span>{user?.username}</span>
            </Space>
          </Dropdown>
        </Header>
        <Content style={{ margin: '24px 16px', padding: 24, background: '#fff' }}>
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  )
}

export default Layout
