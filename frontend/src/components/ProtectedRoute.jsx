import { Navigate } from 'react-router-dom'
import { isAuthenticated, getRole } from '../utils/auth'

export function ProtectedRoute({ children }) {
  if (!isAuthenticated()) return <Navigate to="/login" replace />
  return children
}

export function RoleBasedRoute({ children, roles }) {
  if (!isAuthenticated()) return <Navigate to="/login" replace />
  if (roles && !roles.includes(getRole())) return <Navigate to="/" replace />
  return children
}
