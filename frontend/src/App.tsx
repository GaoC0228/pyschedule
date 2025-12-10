import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import LoginNew from './pages/LoginNew'
import Dashboard from './pages/Dashboard'
import Tasks from './pages/Tasks'
import TaskDetail from './pages/TaskDetail'
import Users from './pages/Users'
import AuditLogs from './pages/AuditLogs'
import AuditCleaner from './pages/AuditCleaner'
import Workspace from './pages/Workspace'
import DatabaseConfig from './pages/DatabaseConfig'
import Profile from './pages/Profile'
import WebTerminalPage from './pages/WebTerminalPage'
import PackageManager from './pages/PackageManager'
import Layout from './components/Layout'
import PrivateRoute from './components/PrivateRoute'

function App() {
  return (
    <AuthProvider>
      <BrowserRouter basename="/python">
        <Routes>
          <Route path="/login" element={<LoginNew />} />
          <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="tasks" element={<Tasks />} />
            <Route path="tasks/:id" element={<TaskDetail />} />
            <Route path="workspace" element={<Workspace />} />
            <Route path="database-config" element={<DatabaseConfig />} />
            <Route path="profile" element={<Profile />} />
            <Route path="users" element={<Users />} />
            <Route path="audit" element={<AuditLogs />} />
            <Route path="audit-cleaner" element={<AuditCleaner />} />
            <Route path="web-terminal" element={<WebTerminalPage />} />
            <Route path="packages" element={<PackageManager />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
