import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Form, Input, Button, Card, message } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useAuth } from '../contexts/AuthContext'
import CLOUDS from 'vanta/dist/vanta.clouds.min'
import * as THREE from 'three'

const Login = () => {
  const [loading, setLoading] = useState(false)
  const [vantaEffect, setVantaEffect] = useState<any>(null)
  const [vantaLoaded, setVantaLoaded] = useState(false)
  const vantaRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()
  const { login } = useAuth()

  useEffect(() => {
    if (!vantaEffect && vantaRef.current) {
      // 延迟加载特效，避免闪烁
      const timer = setTimeout(() => {
        if (vantaRef.current) {
          setVantaEffect(
            CLOUDS({
              el: vantaRef.current as HTMLElement,
              THREE: THREE,
              mouseControls: true,          // 官网参数 - 鼠标控制
              touchControls: true,          // 官网参数 - 触摸控制
              gyroControls: false,          // 官网参数 - 陀螺仪控制
              minHeight: 200.00,            // 官网参数 - 最小高度
              minWidth: 200.00,             // 官网参数 - 最小宽度
              backgroundColor: 0xffffff,    // 官网参数
              skyColor: 0x68b8d7,          // 官网参数
              cloudColor: 0xadc1de,        // 官网参数
              cloudShadowColor: 0x183550,  // 官网参数
              sunColor: 0xff9919,          // 官网参数
              sunGlareColor: 0xff6633,     // 官网参数
              sunlightColor: 0xff9933,     // 官网参数
              speed: 1                      // 官网参数
            })
          )
          setVantaLoaded(true)
        }
      }, 100)
      
      return () => clearTimeout(timer)
    }
    return () => {
      if (vantaEffect) vantaEffect.destroy()
    }
  }, [vantaEffect])

  const onFinish = async (values: any) => {
    setLoading(true)
    try {
      await login(values.username, values.password)
      message.success('登录成功')
      navigate('/dashboard')
    } catch (error: any) {
      // 改进错误提示逻辑
      let errorMessage = '登录失败'
      
      if (error.response) {
        // 服务器返回错误
        errorMessage = error.response.data?.detail || error.response.data?.message || '登录失败，请重试'
      } else if (error.request) {
        // 请求发出但没有响应
        errorMessage = '网络连接失败，请检查网络'
      } else {
        // 其他错误
        errorMessage = error.message || '登录失败，请重试'
      }
      
      console.error('登录错误:', error)
      message.error(errorMessage, 5)  // 显示5秒
    } finally {
      setLoading(false)
    }
  }

  return (
    <div 
      ref={vantaRef}
      style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '100vh',
        width: '100%',
        position: 'fixed',
        top: 0,
        left: 0,
        opacity: vantaLoaded ? 1 : 0,
        transition: 'opacity 0.5s ease-in'
      }}
    >
      <Card 
        style={{ 
          width: 400, 
          boxShadow: '0 12px 40px rgba(0,0,0,0.2)',
          borderRadius: 16,
          backgroundColor: 'rgba(255, 255, 255, 0.98)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.8)',
          transform: vantaLoaded ? 'scale(1)' : 'scale(0.95)',
          transition: 'transform 0.3s ease-out'
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <h1 style={{ 
            fontSize: 32, 
            fontWeight: 'bold', 
            marginBottom: 8,
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}>
            Python定时任务平台
          </h1>
          <p style={{ color: '#666', fontSize: 14 }}>欢迎回来，请登录您的账户</p>
        </div>
        <Form
          name="login"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input prefix={<UserOutlined />} placeholder="用户名" />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <Button type="primary" htmlType="submit" loading={loading} block>
              登录
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

export default Login
