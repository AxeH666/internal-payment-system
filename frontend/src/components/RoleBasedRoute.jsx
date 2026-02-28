import { Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { getCurrentUser } from '../utils/auth'

/**
 * RoleBasedRoute component
 * Redirects to / if user lacks required role
 */
const RoleBasedRoute = ({ children, allowedRoles = [] }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const currentUser = await getCurrentUser()
        setUser(currentUser)
      } catch (error) {
        console.error('Failed to fetch user:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchUser()
  }, [])

  if (loading) {
    return <div>Loading...</div>
  }

  if (!user || (allowedRoles.length > 0 && !allowedRoles.includes(user.role))) {
    return <Navigate to="/" replace />
  }

  return children
}

export default RoleBasedRoute
