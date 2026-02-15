import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../utils/api'
import { handleErrorResponse } from '../utils/errorHandler'
import { getCurrentUser, logout } from '../utils/auth'

/**
 * R7: Pending Requests List Screen
 * Route: /requests
 * Allowed roles: APPROVER
 */
const PendingRequestsList = () => {
  const navigate = useNavigate()
  const [requests, setRequests] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [user, setUser] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const currentUser = await getCurrentUser()
        setUser(currentUser)
        await loadRequests()
      } catch (err) {
        const errorData = handleErrorResponse(err, navigate)
        setError(errorData.message)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [navigate])

  const loadRequests = async () => {
    try {
      const response = await api.get('/requests', { params: { status: 'PENDING_APPROVAL' } })
      setRequests(response.data.data || [])
      setError('')
    } catch (err) {
      const errorData = handleErrorResponse(err, navigate)
      setError(errorData.message)
    }
  }

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
        <h1>Pending Approval Requests</h1>
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

      {requests.length === 0 ? (
        <div style={{ padding: '40px', textAlign: 'center', backgroundColor: 'white', borderRadius: '4px' }}>
          <p>No pending requests.</p>
        </div>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', backgroundColor: 'white', borderRadius: '4px' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #ddd' }}>
              <th style={{ padding: '12px', textAlign: 'left' }}>Batch</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Amount</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Currency</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Beneficiary</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Purpose</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Created</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {requests.map((request) => (
              <tr key={request.id} style={{ borderBottom: '1px solid #eee' }}>
                <td style={{ padding: '12px' }}>{request.batchTitle}</td>
                <td style={{ padding: '12px' }}>{request.amount}</td>
                <td style={{ padding: '12px' }}>{request.currency}</td>
                <td style={{ padding: '12px' }}>{request.beneficiaryName}</td>
                <td style={{ padding: '12px' }}>{request.purpose}</td>
                <td style={{ padding: '12px' }}>{new Date(request.createdAt).toLocaleDateString()}</td>
                <td style={{ padding: '12px' }}>
                  <Link to={`/requests/${request.id}`} style={{ color: '#007bff', textDecoration: 'none' }}>
                    Review
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div style={{ marginTop: '20px' }}>
        <Link to="/batches" style={{ color: '#007bff', textDecoration: 'none', marginRight: '20px' }}>
          View Batches
        </Link>
        <Link to="/audit" style={{ color: '#007bff', textDecoration: 'none' }}>
          View Audit Log
        </Link>
      </div>
    </div>
  )
}

export default PendingRequestsList
