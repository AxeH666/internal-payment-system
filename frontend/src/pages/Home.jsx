import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getCurrentUser } from '../utils/auth'
import { handleErrorResponse } from '../utils/errorHandler'

/**
 * R2: Home Screen
 * Route: /
 * Allowed roles: CREATOR, APPROVER, VIEWER, ADMIN
 * Redirects: CREATOR/VIEWER/ADMIN to /batches; APPROVER to /requests
 */
const Home = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const redirectUser = async () => {
      try {
        const user = await getCurrentUser()
        if (user.role === 'APPROVER') {
          navigate('/requests', { replace: true })
        } else {
          navigate('/batches', { replace: true })
        }
      } catch (err) {
        const errorData = handleErrorResponse(err, navigate)
        if (errorData.message.includes('Session expired')) {
          navigate('/login', { replace: true })
        }
      } finally {
        setLoading(false)
      }
    }

    redirectUser()
  }, [navigate])

  if (loading) {
    return <div style={{ padding: '20px' }}>Loading...</div>
  }

  return null
}

export default Home
