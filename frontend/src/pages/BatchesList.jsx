import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../utils/api'
import { handleErrorResponse } from '../utils/errorHandler'
import { getCurrentUser } from '../utils/auth'
import { logout } from '../utils/auth'

/**
 * R3: Batches List Screen
 * Route: /batches
 * Allowed roles: CREATOR, APPROVER, VIEWER
 */
const BatchesList = () => {
  const navigate = useNavigate()
  const [batches, setBatches] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [user, setUser] = useState(null)
  const [statusFilter, setStatusFilter] = useState('')

  useEffect(() => {
    const fetchData = async () => {
      try {
        const currentUser = await getCurrentUser()
        setUser(currentUser)
        await loadBatches()
      } catch (err) {
        const errorData = handleErrorResponse(err, navigate)
        setError(errorData.message)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [navigate])

  const loadBatches = async () => {
    try {
      const params = {}
      if (statusFilter) {
        params.status = statusFilter
      }
      const response = await api.get('/batches', { params })
      setBatches(response.data.data || [])
      setError('')
    } catch (err) {
      const errorData = handleErrorResponse(err, navigate)
      setError(errorData.message)
    }
  }

  useEffect(() => {
    if (!loading) {
      loadBatches()
    }
  }, [statusFilter])

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  if (loading) {
    return <div style={{ padding: '20px' }}>Loading...</div>
  }

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1>Payment Batches</h1>
        <div>
          {user && <span style={{ marginRight: '15px' }}>Welcome, {user.displayName} ({user.role})</span>}
          <button onClick={handleLogout} style={{ padding: '8px 16px', cursor: 'pointer' }}>
            Logout
          </button>
        </div>
      </div>

      {error && (
        <div style={{ color: 'red', marginBottom: '15px', padding: '10px', backgroundColor: '#ffe6e6', borderRadius: '4px' }}>
          {error}
        </div>
      )}

      <div style={{ marginBottom: '20px' }}>
        {user?.role === 'CREATOR' && (
          <Link to="/batches/new" style={{ display: 'inline-block', padding: '10px 20px', backgroundColor: '#007bff', color: 'white', textDecoration: 'none', borderRadius: '4px', marginRight: '10px' }}>
            Create Batch
          </Link>
        )}
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          style={{ padding: '8px', fontSize: '14px' }}
        >
          <option value="">All Statuses</option>
          <option value="DRAFT">Draft</option>
          <option value="SUBMITTED">Submitted</option>
          <option value="PROCESSING">Processing</option>
          <option value="COMPLETED">Completed</option>
          <option value="CANCELLED">Cancelled</option>
        </select>
      </div>

      {batches.length === 0 ? (
        <div style={{ padding: '40px', textAlign: 'center', backgroundColor: 'white', borderRadius: '4px' }}>
          <p>No batches yet.</p>
          {user?.role === 'CREATOR' && (
            <Link to="/batches/new" style={{ display: 'inline-block', marginTop: '15px', padding: '10px 20px', backgroundColor: '#007bff', color: 'white', textDecoration: 'none', borderRadius: '4px' }}>
              Create Batch
            </Link>
          )}
        </div>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', backgroundColor: 'white', borderRadius: '4px' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #ddd' }}>
              <th style={{ padding: '12px', textAlign: 'left' }}>Title</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Status</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Created</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Request Count</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {batches.map((batch) => (
              <tr key={batch.id} style={{ borderBottom: '1px solid #eee' }}>
                <td style={{ padding: '12px' }}>{batch.title}</td>
                <td style={{ padding: '12px' }}>{batch.status}</td>
                <td style={{ padding: '12px' }}>{new Date(batch.createdAt).toLocaleDateString()}</td>
                <td style={{ padding: '12px' }}>{batch.requestCount || 0}</td>
                <td style={{ padding: '12px' }}>
                  <Link to={`/batches/${batch.id}`} style={{ color: '#007bff', textDecoration: 'none' }}>
                    View
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div style={{ marginTop: '20px' }}>
        <Link to="/audit" style={{ color: '#007bff', textDecoration: 'none' }}>
          View Audit Log
        </Link>
      </div>
    </div>
  )
}

export default BatchesList
