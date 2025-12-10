import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { Spin } from 'antd'

interface PrivateRouteProps {
  children: React.ReactNode
}

const PrivateRoute: React.FC<PrivateRouteProps> = ({ children }) => {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" />
      </div>
    )
  }

  return user ? <>{children}</> : <Navigate to="/login" replace />
}

export default PrivateRoute
