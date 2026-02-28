import { useState, useEffect } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import api from '../utils/api'
import { handleErrorResponse } from '../utils/errorHandler'
import { getCurrentUser } from '../utils/auth'
import { getBatchActionVisibility } from '../utils/stateVisibility'

/**
 * R5: Batch Detail Screen
 * Route: /batches/:batchId
 * Allowed roles: CREATOR, APPROVER, VIEWER
 */
const BatchDetail = () => {
  const navigate = useNavigate()
  const { batchId } = useParams()
  const [batch, setBatch] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [user, setUser] = useState(null)
  const [actionLoading, setActionLoading] = useState('')
  const [showAddRequestForm, setShowAddRequestForm] = useState(false)
  const [newRequestData, setNewRequestData] = useState({
    amount: '',
    currency: 'USD',
    beneficiaryName: '',
    beneficiaryAccount: '',
    purpose: '',
  })

  useEffect(() => {
    const fetchData = async () => {
      try {
        const currentUser = await getCurrentUser()
        setUser(currentUser)
        await loadBatch()
      } catch (err) {
        const errorData = handleErrorResponse(err, navigate)
        setError(errorData.message)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [batchId, navigate])

  const loadBatch = async () => {
    try {
      const response = await api.get(`/batches/${batchId}`)
      setBatch(response.data.data)
      setError('')
    } catch (err) {
      const errorData = handleErrorResponse(err, navigate)
      if (errorData.shouldReload) {
        await loadBatch()
      }
      setError(errorData.message)
    }
  }

  const handleSubmitBatch = async () => {
    setActionLoading('submit')
    setError('')
    try {
      const response = await api.post(`/batches/${batchId}/submit`, {})
      setBatch(response.data.data)
    } catch (err) {
      const errorData = handleErrorResponse(err, navigate)
      if (errorData.shouldReload) {
        await loadBatch()
      }
      setError(errorData.message)
    } finally {
      setActionLoading('')
    }
  }

  const handleCancelBatch = async () => {
    setActionLoading('cancel')
    setError('')
    try {
      const response = await api.post(`/batches/${batchId}/cancel`, {})
      setBatch(response.data.data)
    } catch (err) {
      const errorData = handleErrorResponse(err, navigate)
      if (errorData.shouldReload) {
        await loadBatch()
      }
      setError(errorData.message)
    } finally {
      setActionLoading('')
    }
  }

  const handleAddRequest = async (e) => {
    e.preventDefault()
    setActionLoading('addRequest')
    setError('')
    try {
      const response = await api.post(`/batches/${batchId}/requests`, newRequestData)
      await loadBatch()
      setShowAddRequestForm(false)
      setNewRequestData({
        amount: '',
        currency: 'USD',
        beneficiaryName: '',
        beneficiaryAccount: '',
        purpose: '',
      })
    } catch (err) {
      const errorData = handleErrorResponse(err, navigate)
      if (errorData.shouldReload) {
        await loadBatch()
      }
      setError(errorData.message)
    } finally {
      setActionLoading('')
    }
  }

  if (loading) {
    return <div style={{ padding: '20px' }}>Loading...</div>
  }

  if (!batch) {
    return (
      <div style={{ padding: '20px' }}>
        <p>Batch not found.</p>
        <Link to="/batches">Back to Batches</Link>
      </div>
    )
  }

  const visibility = getBatchActionVisibility(batch, user)
  const requests = batch.requests || []
  const liveSoaSummary = batch.liveSoaSummary || []

  const handleExportSOA = async (format) => {
    setActionLoading(`export-${format}`)
    setError('')
    try {
      const response = await api.get(`/batches/${batchId}/soa-export?format=${format}`, {
        responseType: 'blob',
      })
      const ext = format === 'pdf' ? 'pdf' : 'xlsx'
      const blob = new Blob([response.data], {
        type: response.headers['content-type'] || (format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
      })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `soa_export_${batch.title.replace(/\s/g, '_')}_${new Date().toISOString().slice(0, 10)}.${ext}`
      link.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      const errorData = handleErrorResponse(err, navigate)
      setError(errorData.message)
    } finally {
      setActionLoading('')
    }
  }

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ marginBottom: '20px' }}>
        <Link to="/batches" style={{ color: '#007bff', textDecoration: 'none' }}>
          ← Back to Batches
        </Link>
      </div>

      <h1>{batch.title}</h1>
      <div style={{ marginBottom: '20px' }}>
        <p><strong>Status:</strong> {batch.status}</p>
        <p><strong>Batch Total:</strong> {batch.batchTotal || '0'} (sum of request amounts)</p>
        <p><strong>Created:</strong> {new Date(batch.createdAt).toLocaleString()}</p>
        {batch.submittedAt && <p><strong>Submitted:</strong> {new Date(batch.submittedAt).toLocaleString()}</p>}
        {batch.completedAt && <p><strong>Completed:</strong> {new Date(batch.completedAt).toLocaleString()}</p>}
      </div>

      {error && (
        <div style={{ color: 'red', marginBottom: '15px', padding: '10px', backgroundColor: '#ffe6e6', borderRadius: '4px' }}>
          {error}
        </div>
      )}

      <div style={{ marginBottom: '20px', display: 'flex', gap: '10px' }}>
        {visibility.submitButton && (
          <button
            onClick={handleSubmitBatch}
            disabled={actionLoading !== ''}
            style={{ padding: '10px 20px', fontSize: '16px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px', cursor: actionLoading !== '' ? 'not-allowed' : 'pointer' }}
          >
            {actionLoading === 'submit' ? 'Submitting...' : 'Submit Batch'}
          </button>
        )}
        {visibility.cancelButton && (
          <button
            onClick={handleCancelBatch}
            disabled={actionLoading !== ''}
            style={{ padding: '10px 20px', fontSize: '16px', backgroundColor: '#dc3545', color: 'white', border: 'none', borderRadius: '4px', cursor: actionLoading !== '' ? 'not-allowed' : 'pointer' }}
          >
            {actionLoading === 'cancel' ? 'Cancelling...' : 'Cancel Batch'}
          </button>
        )}
        {visibility.addRequestButton && !showAddRequestForm && (
          <button
            onClick={() => setShowAddRequestForm(true)}
            disabled={actionLoading !== ''}
            style={{ padding: '10px 20px', fontSize: '16px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: actionLoading !== '' ? 'not-allowed' : 'pointer' }}
          >
            Add Request
          </button>
        )}
        <button
          onClick={() => handleExportSOA('pdf')}
          disabled={actionLoading !== ''}
          title="Export SOA as PDF (immutable snapshot)"
          style={{ padding: '10px 20px', fontSize: '16px', backgroundColor: '#6f42c1', color: 'white', border: 'none', borderRadius: '4px', cursor: actionLoading !== '' ? 'not-allowed' : 'pointer' }}
        >
          {actionLoading === 'export-pdf' ? 'Exporting...' : 'Export PDF'}
        </button>
        <button
          onClick={() => handleExportSOA('excel')}
          disabled={actionLoading !== ''}
          title="Export SOA as Excel (immutable snapshot)"
          style={{ padding: '10px 20px', fontSize: '16px', backgroundColor: '#20c997', color: 'white', border: 'none', borderRadius: '4px', cursor: actionLoading !== '' ? 'not-allowed' : 'pointer' }}
        >
          {actionLoading === 'export-excel' ? 'Exporting...' : 'Export Excel'}
        </button>
      </div>

      {liveSoaSummary.length > 0 && (
        <div style={{ backgroundColor: '#f8f9fa', padding: '20px', borderRadius: '4px', marginBottom: '20px' }}>
          <h2>Live SOA Summary</h2>
          <p style={{ color: '#6c757d', marginBottom: '15px' }}>Current SOA status per request (always latest)</p>
          <table style={{ width: '100%', borderCollapse: 'collapse', backgroundColor: 'white' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #ddd' }}>
                <th style={{ padding: '12px', textAlign: 'left' }}>Beneficiary</th>
                <th style={{ padding: '12px', textAlign: 'left' }}>Amount</th>
                <th style={{ padding: '12px', textAlign: 'left' }}>Currency</th>
                <th style={{ padding: '12px', textAlign: 'left' }}>SOA Status</th>
                <th style={{ padding: '12px', textAlign: 'left' }}>Latest Version</th>
                <th style={{ padding: '12px', textAlign: 'left' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {liveSoaSummary.map((item) => (
                <tr key={item.requestId} style={{ borderBottom: '1px solid #eee' }}>
                  <td style={{ padding: '12px' }}>{item.beneficiaryName}</td>
                  <td style={{ padding: '12px' }}>{item.amount}</td>
                  <td style={{ padding: '12px' }}>{item.currency}</td>
                  <td style={{ padding: '12px' }}>
                    {item.hasSoa ? (
                      <span style={{ color: '#28a745' }}>✓ Has SOA</span>
                    ) : (
                      <span style={{ color: '#dc3545' }}>No SOA</span>
                    )}
                  </td>
                  <td style={{ padding: '12px' }}>
                    {item.latestVersion
                      ? `v${item.latestVersion} (${item.latestUploadedAt ? new Date(item.latestUploadedAt).toLocaleString() : ''})`
                      : '—'}
                  </td>
                  <td style={{ padding: '12px' }}>
                    <Link to={`/batches/${batchId}/requests/${item.requestId}`} style={{ color: '#007bff', textDecoration: 'none' }}>
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showAddRequestForm && visibility.addRequestButton && (
        <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '4px', marginBottom: '20px' }}>
          <h2>Add Payment Request</h2>
          <form onSubmit={handleAddRequest}>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px' }}>Amount</label>
              <input
                type="text"
                value={newRequestData.amount}
                onChange={(e) => setNewRequestData({ ...newRequestData, amount: e.target.value })}
                required
                disabled={actionLoading !== ''}
                style={{ width: '100%', padding: '8px' }}
              />
            </div>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px' }}>Currency</label>
              <input
                type="text"
                value={newRequestData.currency}
                onChange={(e) => setNewRequestData({ ...newRequestData, currency: e.target.value })}
                required
                disabled={actionLoading !== ''}
                style={{ width: '100%', padding: '8px' }}
              />
            </div>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px' }}>Beneficiary Name</label>
              <input
                type="text"
                value={newRequestData.beneficiaryName}
                onChange={(e) => setNewRequestData({ ...newRequestData, beneficiaryName: e.target.value })}
                required
                disabled={actionLoading !== ''}
                style={{ width: '100%', padding: '8px' }}
              />
            </div>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px' }}>Beneficiary Account</label>
              <input
                type="text"
                value={newRequestData.beneficiaryAccount}
                onChange={(e) => setNewRequestData({ ...newRequestData, beneficiaryAccount: e.target.value })}
                required
                disabled={actionLoading !== ''}
                style={{ width: '100%', padding: '8px' }}
              />
            </div>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px' }}>Purpose</label>
              <textarea
                value={newRequestData.purpose}
                onChange={(e) => setNewRequestData({ ...newRequestData, purpose: e.target.value })}
                required
                disabled={actionLoading !== ''}
                style={{ width: '100%', padding: '8px', minHeight: '80px' }}
              />
            </div>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                type="submit"
                disabled={actionLoading !== ''}
                style={{ padding: '10px 20px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px', cursor: actionLoading !== '' ? 'not-allowed' : 'pointer' }}
              >
                {actionLoading === 'addRequest' ? 'Adding...' : 'Add Request'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowAddRequestForm(false)
                  setNewRequestData({
                    amount: '',
                    currency: 'USD',
                    beneficiaryName: '',
                    beneficiaryAccount: '',
                    purpose: '',
                  })
                }}
                disabled={actionLoading !== ''}
                style={{ padding: '10px 20px', backgroundColor: '#6c757d', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <h2>Payment Requests</h2>
      {requests.length === 0 ? (
        <div style={{ padding: '40px', textAlign: 'center', backgroundColor: 'white', borderRadius: '4px' }}>
          <p>No payment requests in this batch.</p>
          {visibility.addRequestButton && !showAddRequestForm && (
            <button
              onClick={() => setShowAddRequestForm(true)}
              style={{ marginTop: '15px', padding: '10px 20px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
            >
              Add Request
            </button>
          )}
        </div>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', backgroundColor: 'white', borderRadius: '4px' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #ddd' }}>
              <th style={{ padding: '12px', textAlign: 'left' }}>Amount</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Currency</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Beneficiary</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Purpose</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Status</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {requests.map((request) => (
              <tr key={request.id} style={{ borderBottom: '1px solid #eee' }}>
                <td style={{ padding: '12px' }}>{request.amount}</td>
                <td style={{ padding: '12px' }}>{request.currency}</td>
                <td style={{ padding: '12px' }}>{request.beneficiaryName}</td>
                <td style={{ padding: '12px' }}>{request.purpose}</td>
                <td style={{ padding: '12px' }}>{request.status}</td>
                <td style={{ padding: '12px' }}>
                  <Link to={`/batches/${batchId}/requests/${request.id}`} style={{ color: '#007bff', textDecoration: 'none' }}>
                    View
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

export default BatchDetail
