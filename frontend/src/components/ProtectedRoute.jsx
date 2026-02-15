import { Navigate } from 'react-router-dom'
import { isAuthenticated } from '../utils/auth'

/**
 * ProtectedRoute component
 * Redirects to /login if user is not authenticated
 */
const ProtectedRoute = ({ children, allowedRoles = [] }) => {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />
  }

  return children
}

export default ProtectedRoute
