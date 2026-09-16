import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function RequireAdmin() {
  const { user, loading } = useAuth()

  if (loading) {
    return null
  }
  if (!user) {
    return <Navigate to="/login" replace />
  }
  if (!user.is_admin) {
    return <Navigate to="/" replace />
  }
  return <Outlet />
}

export default RequireAdmin
