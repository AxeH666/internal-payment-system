import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../utils/api'
import { handleErrorResponse } from '../utils/errorHandler'
import { getCurrentUser } from '../utils/auth'

/**
 * R9: Audit Log Screen
 * Route: /audit
 * Allowed roles: CREATOR, APPROVER, VIEWER
 */
const AuditLog = () => {
  const navigate = useNavigate()
  const [auditEntries, setAuditEntries] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [user, setUser] = useState(null)
  const [filters, setFilters] = useState({
    entityType: '',
    entityId: '',
    actorId: '',
    fromDate: '',
    toDate: '',
  })

  useEffect(() => {
    const fetchData = async () => {
      try {
        const currentUser = await getCurrentUser()
        setUser(currentUser)
        await loadAuditLog()
      } catch (err) {
        const errorData = handleErrorResponse(err, navigate)
        setError(errorData.message)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [navigate])

  const loadAuditLog = async () => {
    try {
      const params = {}
      if (filters.entityType) params.entityType = filters.entityType
      if (filters.entityId) params.entityId = filters.entityId
      if (filters.actorId) params.actorId = filters.actorId
      if (filters.fromDate) params.fromDate = filters.fromDate
      if (filters.toDate) params.toDate = filters.toDate

      const response = await api.get('/audit', { params })
      setAuditEntries(response.data.data || [])
      setError('')
    } catch (err) {
      const errorData = handleErrorResponse(err, navigate)
      setError(errorData.message)
    }
  }

  useEffect(() => {
    if (!loading) {
      loadAuditLog()
    }
  }, [filters])

  const handleFilterChange = (field, value) => {
    setFilters({ ...filters, [field]: value })
  }

  if (loading) {
    return <div style={{ padding: '20px' }}>Loading...</div>
  }

  return (
    <div style={{ padding: '20px', maxWidth: '1400px', margin: '0 auto' }}>
      <h1 style={{ marginBottom: '20px' }}>Audit Log</h1>

      {error && (
        <div style={{ color: 'red', marginBottom: '15px', padding: '10px', backgroundColor: '#ffe6e6', borderRadius: '4px' }}>
          {error}
        </div>
      )}

      <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '4px', marginBottom: '20px' }}>
        <h2>Filters</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '5px' }}>Entity Type</label>
            <select
              value={filters.entityType}
              onChange={(e) => handleFilterChange('entityType', e.target.value)}
              style={{ width: '100%', padding: '8px' }}
            >
              <option value="">All</option>
              <option value="PaymentBatch">PaymentBatch</option>
              <option value="PaymentRequest">PaymentRequest</option>
            </select>
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '5px' }}>Entity ID</label>
            <input
              type="text"
              value={filters.entityId}
              onChange={(e) => handleFilterChange('entityId', e.target.value)}
              style={{ width: '100%', padding: '8px' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '5px' }}>Actor ID</label>
            <input
              type="text"
              value={filters.actorId}
              onChange={(e) => handleFilterChange('actorId', e.target.value)}
              style={{ width: '100%', padding: '8px' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '5px' }}>From Date</label>
            <input
              type="date"
              value={filters.fromDate}
              onChange={(e) => handleFilterChange('fromDate', e.target.value)}
              style={{ width: '100%', padding: '8px' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '5px' }}>To Date</label>
            <input
              type="date"
              value={filters.toDate}
              onChange={(e) => handleFilterChange('toDate', e.target.value)}
              style={{ width: '100%', padding: '8px' }}
            />
          </div>
        </div>
      </div>

      {auditEntries.length === 0 ? (
        <div style={{ padding: '40px', textAlign: 'center', backgroundColor: 'white', borderRadius: '4px' }}>
          <p>No audit entries match your filters.</p>
        </div>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', backgroundColor: 'white', borderRadius: '4px' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #ddd' }}>
              <th style={{ padding: '12px', textAlign: 'left' }}>Event Type</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Entity Type</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Entity ID</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Actor ID</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Previous State</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>New State</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Occurred At</th>
            </tr>
          </thead>
          <tbody>
            {auditEntries.map((entry) => (
              <tr key={entry.id} style={{ borderBottom: '1px solid #eee' }}>
                <td style={{ padding: '12px' }}>{entry.eventType}</td>
                <td style={{ padding: '12px' }}>{entry.entityType}</td>
                <td style={{ padding: '12px' }}>{entry.entityId}</td>
                <td style={{ padding: '12px' }}>{entry.actorId}</td>
                <td style={{ padding: '12px' }}>{entry.previousState || '-'}</td>
                <td style={{ padding: '12px' }}>{entry.newState || '-'}</td>
                <td style={{ padding: '12px' }}>{new Date(entry.occurredAt).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div style={{ marginTop: '20px' }}>
        <Link to="/batches" style={{ color: '#007bff', textDecoration: 'none', marginRight: '20px' }}>
          View Batches
        </Link>
        {user?.role === 'APPROVER' && (
          <Link to="/requests" style={{ color: '#007bff', textDecoration: 'none', marginRight: '20px' }}>
            View Pending Requests
          </Link>
        )}
      </div>
    </div>
  )
}

export default AuditLog
