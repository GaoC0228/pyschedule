import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 300000, // 5分钟超时
  maxContentLength: 500 * 1024 * 1024, // 500MB
  maxBodyLength: 500 * 1024 * 1024, // 500MB
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      // 只在非登录页面才清除token并跳转
      // 如果是登录接口本身的401错误，不应该触发重定向
      const currentPath = window.location.pathname
      const isLoginPage = currentPath.includes('/login')
      const isLoginRequest = error.config?.url?.includes('/auth/login')
      
      if (!isLoginPage && !isLoginRequest) {
        localStorage.removeItem('token')
        window.location.href = '/python/login'
      } else if (!isLoginRequest) {
        // 如果在登录页但不是登录请求，清除token但不跳转
        localStorage.removeItem('token')
      }
      // 登录请求的401错误直接抛出，让登录页面自己处理
    }
    return Promise.reject(error)
  }
)

export default api
