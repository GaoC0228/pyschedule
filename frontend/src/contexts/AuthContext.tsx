import React, { createContext, useContext, useState, useEffect } from 'react'
import api from '../api/axios'

interface User {
  id: number
  username: string
  email: string
  role: string
  is_active: boolean
  can_manage_packages?: boolean
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  register: (username: string, email: string, password: string) => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      fetchUser()
    } else {
      setLoading(false)
    }
  }, [])

  const fetchUser = async () => {
    try {
      const response = await api.get('/auth/me')
      setUser(response.data)
    } catch (error) {
      localStorage.removeItem('token')
    } finally {
      setLoading(false)
    }
  }

  const login = async (username: string, password: string) => {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    
    const response = await api.post('/auth/login', formData)
    localStorage.setItem('token', response.data.access_token)
    await fetchUser()
  }

  const logout = async () => {
    try {
      // 调用后端登出接口，清除在线状态
      await api.post('/auth/logout')
    } catch (error) {
      // 即使后端调用失败也要清除本地token
      console.error('登出失败:', error)
    } finally {
      // 清除本地token和用户信息
      localStorage.removeItem('token')
      setUser(null)
    }
  }

  const register = async (username: string, email: string, password: string) => {
    await api.post('/auth/register', { username, email, password })
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, register }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
