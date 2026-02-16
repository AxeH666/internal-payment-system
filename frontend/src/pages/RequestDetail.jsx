import { useState, useEffect } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import api from '../utils/api'
import { handleErrorResponse } from '../utils/errorHandler'
import { getCurrentUser } from '../utils/auth'
import { getRequestActionVisibility } from '../utils/stateVisibility'

/**
 * R6: Payment Request Detail (from batch context)
 * Route: /batches/:batchId/requests/:requestId
 * Allowed roles: CREATOR, APPROVER, VIEWER
 */
const RequestDetail = () => {
  const navigate = useNavigate()
  const { batchId, requestId } = useParams()
  const [request, setRequest] = useState(null)
  const [batch, setBatch] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [user, setUser] = useState(null)
  const [actionLoading, setActionLoading] = useState('')
  const [showEditForm, setShowEditForm] = useState(false)
  const [editFormData, setEditFormData] = useState({})

  useEffect(() => {
    const fetchData = async () => {
      try {
        const currentUser = await getCurrentUser()
        setUser(currentUser)
        await loadRequest()
        await loadBatch()
      } catch (err) {
        const errorData = handleErrorResponse(err, navigate)
        setError(errorData.message)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [batchId, requestId, navigate])

  const loadRequest = async () => {
    try {
      const response = await api.get(`/batches/${batchId}/requests/${requestId}`)
      setRequest(response.data.data)
      setEditFormData({
        amount: response.data.data.amount,
        currency: response.data.data.currency,
        beneficiaryName: response.data.data.beneficiaryName,
        beneficiaryAccount: response.data.data.beneficiaryAccount,
        purpose: response.data.data.purpose,
      })
      setError('')
    } catch (err) {
      const errorData = handleErrorResponse(err, navigate)
      if (errorData.shouldReload) {
        await loadRequest()
      }
      setError(errorData.message)
    }
  }

  const loadBatch = async () => {
    try {
      const response = await api.get(`/batches/${batchId}`)
      setBatch(response.data.data)
    } catch (err) {
      console.error('Failed to load batch:', err)
    }
  }

  const handleUpdateRequest = async () => {
    setActionLoading('update')
    setError('')
    try {
      const response = await api.patch(`/batches/${batchId}/requests/${requestId}`, editFormData)
      setRequest(response.data.data)
      setShowEditForm(false)
    } catch (err) {
      const errorData = handleErrorResponse(err, navigate)
      if (errorData.shouldReload) {
        await loadRequest()
      }
      setError(errorData.message)
    } finally {
      setActionLoading('')
    }
  }

  const handleApprove = async () => {
    setActionLoading('approve')
    setError('')
    try {
      const response = await api.post(`/requests/${requestId}/approve`, { comment: '' })
      setRequest(response.data.data)
      await loadBatch()
    } catch (err) {
      const errorData = handleErrorResponse(err, navigate)
      if (errorData.shouldReload) {
        await loadRequest()
        await loadBatch()
      }
      setError(errorData.message)
    } finally {
      setActionLoading('')
    }
  }

  const handleReject = async () => {
    setActionLoading('reject')
    setError('')
    try {
      const response = await api.post(`/requests/${requestId}/reject`, { comment: '' })
      setRequest(response.data.data)
      await loadBatch()
    } catch (err) {
      const errorData = handleErrorResponse(err, navigate)
      if (errorData.shouldReload) {
        await loadRequest()
        await loadBatch()
      }
      setError(errorData.message)
    } finally {
      setActionLoading('')
    }
  }

  const handleMarkPaid = async () => {
    setActionLoading('markPaid')
    setError('')
    try {
      const response = await api.post(`/requests/${requestId}/mark-paid`, {})
      setRequest(response.data.data)
      await loadBatch()
    } catch (err) {
      const errorData = handleErrorResponse(err, navigate)
      if (errorData.shouldReload) {
        await loadRequest()
        await loadBatch()
      }
      setError(errorData.message)
    } finally {
      setActionLoading('')
    }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    setActionLoading('upload')
    setError('')
    try {
      const formData = new FormData()
      formData.append('file', file)
      await api.post(`/batches/${batchId}/requests/${requestId}/soa`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      await loadRequest()
    } catch (err) {
      const errorData = handleErrorResponse(err, navigate)
      if (errorData.shouldReload) {
        await loadRequest()
      }
      setError(errorData.message)
    } finally {
      setActionLoading('')
    }
  }

  if (loading) {
    return <div style={{ padding: '20px' }}>Loading...</div>
  }

  if (!request) {
    return (
      <div style={{ padding: '20px' }}>
        <p>Request not found.</p>
        <Link to={`/batches/${batchId}`}>Back to Batch</Link>
      </div>
    )
  }

  const visibility = getRequestActionVisibility(request, batch, user)
  const soaVersions = request.soaVersions || []

  return (
    <div style={{ padding: '20px', maxWidth: '1000px', margin: '0 auto' }}>
      <div style={{ marginBottom: '20px' }}>
        <Link to={`/batches/${batchId}`} style={{ color: '#007bff', textDecoration: 'none' }}>
          ← Back to Batch
        </Link>
      </div>

      <h1>Payment Request</h1>

      {error && (
        <div style={{ color: 'red', marginBottom: '15px', padding: '10px', backgroundColor: '#ffe6e6', borderRadius: '4px' }}>
          {error}
        </div>
      )}

      {showEditForm ? (
        <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '4px', marginBottom: '20px' }}>
          <h2>Edit Request</h2>
          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px' }}>Amount</label>
            <input
              type="text"
              value={editFormData.amount}
              onChange={(e) => setEditFormData({ ...editFormData, amount: e.target.value })}
              style={{ width: '100%', padding: '8px' }}
            />
          </div>
          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px' }}>Currency</label>
            <input
              type="text"
              value={editFormData.currency}
              onChange={(e) => setEditFormData({ ...editFormData, currency: e.target.value })}
              style={{ width: '100%', padding: '8px' }}
            />
          </div>
          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px' }}>Beneficiary Name</label>
            <input
              type="text"
              value={editFormData.beneficiaryName}
              onChange={(e) => setEditFormData({ ...editFormData, beneficiaryName: e.target.value })}
              style={{ width: '100%', padding: '8px' }}
            />
          </div>
          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px' }}>Beneficiary Account</label>
            <input
              type="text"
              value={editFormData.beneficiaryAccount}
              onChange={(e) => setEditFormData({ ...editFormData, beneficiaryAccount: e.target.value })}
              style={{ width: '100%', padding: '8px' }}
            />
          </div>
          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px' }}>Purpose</label>
            <textarea
              value={editFormData.purpose}
              onChange={(e) => setEditFormData({ ...editFormData, purpose: e.target.value })}
              style={{ width: '100%', padding: '8px', minHeight: '80px' }}
            />
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={handleUpdateRequest}
              disabled={actionLoading !== ''}
              style={{ padding: '10px 20px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
            >
              Save
            </button>
            <button
              onClick={() => setShowEditForm(false)}
              disabled={actionLoading !== ''}
              style={{ padding: '10px 20px', backgroundColor: '#6c757d', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '4px', marginBottom: '20px' }}>
          <div style={{ marginBottom: '15px' }}>
            <p><strong>Amount:</strong> {request.amount} {request.currency}</p>
            <p><strong>Beneficiary:</strong> {request.beneficiaryName}</p>
            <p><strong>Account:</strong> {request.beneficiaryAccount}</p>
            <p><strong>Purpose:</strong> {request.purpose}</p>
            <p><strong>Status:</strong> {request.status}</p>
            <p><strong>Created:</strong> {new Date(request.createdAt).toLocaleString()}</p>
            {request.updatedAt && <p><strong>Updated:</strong> {new Date(request.updatedAt).toLocaleString()}</p>}
            {request.approval && (
              <div style={{ marginTop: '15px', padding: '10px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
                <p><strong>Approval Decision:</strong> {request.approval.decision}</p>
                {request.approval.comment && <p><strong>Comment:</strong> {request.approval.comment}</p>}
                <p><strong>Approved At:</strong> {new Date(request.approval.createdAt).toLocaleString()}</p>
              </div>
            )}
          </div>

          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            {visibility.editButton && (
              <button
                onClick={() => setShowEditForm(true)}
                disabled={actionLoading !== ''}
                style={{ padding: '10px 20px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
              >
                Edit
              </button>
            )}
            {visibility.uploadSoaButton && (
              <label style={{ padding: '10px 20px', backgroundColor: '#17a2b8', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', display: 'inline-block' }}>
                Upload SOA
                <input type="file" onChange={handleFileUpload} style={{ display: 'none' }} disabled={actionLoading !== ''} />
              </label>
            )}
            {visibility.approveButton && (
              <button
                onClick={handleApprove}
                disabled={actionLoading !== ''}
                style={{ padding: '10px 20px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px', cursor: actionLoading !== '' ? 'not-allowed' : 'pointer' }}
              >
                {actionLoading === 'approve' ? 'Approving...' : 'Approve'}
              </button>
            )}
            {visibility.rejectButton && (
              <button
                onClick={handleReject}
                disabled={actionLoading !== ''}
                style={{ padding: '10px 20px', backgroundColor: '#dc3545', color: 'white', border: 'none', borderRadius: '4px', cursor: actionLoading !== '' ? 'not-allowed' : 'pointer' }}
              >
                {actionLoading === 'reject' ? 'Rejecting...' : 'Reject'}
              </button>
            )}
            {visibility.markPaidButton && (
              <button
                onClick={handleMarkPaid}
                disabled={actionLoading !== ''}
                style={{ padding: '10px 20px', backgroundColor: '#ffc107', color: 'black', border: 'none', borderRadius: '4px', cursor: actionLoading !== '' ? 'not-allowed' : 'pointer' }}
              >
                {actionLoading === 'markPaid' ? 'Marking...' : 'Mark Paid'}
              </button>
            )}
          </div>
        </div>
      )}

      <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '4px' }}>
        <h2>Statement of Account Documents</h2>
        <p style={{ color: '#6c757d', marginBottom: '15px' }}>
          Version history — each version is immutable. Final SOA locks at submission.
        </p>
        {soaVersions.length === 0 ? (
          <p>No Statement of Account documents.</p>
        ) : (
          <div>
            {soaVersions.map((soa) => (
              <div
                key={soa.id}
                style={{
                  marginBottom: '16px',
                  padding: '12px',
                  backgroundColor: '#f8f9fa',
                  borderRadius: '4px',
                  borderLeft: '4px solid #007bff',
                }}
              >
                <div style={{ fontWeight: 'bold', marginBottom: '6px' }}>
                  Version {soa.versionNumber}
                  {soa.source === 'GENERATED' && (
                    <span style={{ marginLeft: '8px', fontSize: '12px', color: '#6c757d', backgroundColor: '#e9ecef', padding: '2px 6px', borderRadius: '4px' }}>
                      Auto-generated
                    </span>
                  )}
                  {' — '}
                  {soa.changeSummary || `Uploaded ${new Date(soa.uploadedAt).toLocaleString()}`}
                </div>
                {soa.downloadUrl && (
                  <a
                    href="#"
                    style={{ color: '#007bff', textDecoration: 'none', fontSize: '14px' }}
                    onClick={(e) => {
                      e.preventDefault()
                      const apiPath = (soa.downloadUrl.split('/api/v1')[1] || soa.downloadUrl).replace(/^\//, '')
                      api.get(apiPath, { responseType: 'blob' })
                        .then((res) => {
                          const url = URL.createObjectURL(new Blob([res.data]))
                          const link = document.createElement('a')
                          link.href = url
                          link.download = `soa_v${soa.versionNumber}.pdf`
                          link.click()
                          URL.revokeObjectURL(url)
                        })
                        .catch(() => setError('Download failed'))
                    }}
                  >
                    Download v{soa.versionNumber}
                  </a>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default RequestDetail
