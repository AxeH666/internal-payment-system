import { useState, useEffect } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import api from '../utils/api'
import { handleErrorResponse } from '../utils/errorHandler'
import { getCurrentUser } from '../utils/auth'
import { getRequestApprovalQueueVisibility } from '../utils/stateVisibility'

/**
 * R8: Payment Request Detail (from approval queue)
 * Route: /requests/:requestId
 * Allowed roles: APPROVER
 */
const RequestDetailApprovalQueue = () => {
  const navigate = useNavigate()
  const { requestId } = useParams()
  const [request, setRequest] = useState(null)
  const [batchId, setBatchId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [user, setUser] = useState(null)
  const [actionLoading, setActionLoading] = useState('')

  useEffect(() => {
    const fetchData = async () => {
      try {
        const currentUser = await getCurrentUser()
        setUser(currentUser)
        await loadRequest()
      } catch (err) {
        const errorData = handleErrorResponse(err, navigate)
        setError(errorData.message)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [requestId, navigate])

  const loadRequest = async () => {
    try {
      // First get request from /requests endpoint to get batchId
      const listResponse = await api.get('/requests', { params: { status: 'PENDING_APPROVAL' } })
      const requestFromList = listResponse.data.data.find((r) => r.id === requestId)
      
      if (!requestFromList) {
        // Try to get from batch context if we have batchId
        if (batchId) {
          const response = await api.get(`/batches/${batchId}/requests/${requestId}`)
          setRequest(response.data.data)
          setBatchId(response.data.data.batchId)
        } else {
          throw new Error('Request not found')
        }
      } else {
        setBatchId(requestFromList.batchId)
        const response = await api.get(`/batches/${requestFromList.batchId}/requests/${requestId}`)
        setRequest(response.data.data)
      }
      setError('')
    } catch (err) {
      const errorData = handleErrorResponse(err, navigate)
      if (errorData.shouldReload) {
        await loadRequest()
      }
      setError(errorData.message)
    }
  }

  const handleApprove = async () => {
    setActionLoading('approve')
    setError('')
    try {
      const response = await api.post(`/requests/${requestId}/approve`, { comment: '' })
      setRequest(response.data.data)
      navigate('/requests')
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

  const handleReject = async () => {
    setActionLoading('reject')
    setError('')
    try {
      const response = await api.post(`/requests/${requestId}/reject`, { comment: '' })
      setRequest(response.data.data)
      navigate('/requests')
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

  const handleMarkPaid = async () => {
    setActionLoading('markPaid')
    setError('')
    try {
      const response = await api.post(`/requests/${requestId}/mark-paid`, {})
      setRequest(response.data.data)
      navigate('/requests')
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
        <Link to="/requests">Back to Pending Requests</Link>
      </div>
    )
  }

  const visibility = getRequestApprovalQueueVisibility(request, user)
  const soaVersions = request.soaVersions || []

  return (
    <div style={{ padding: '20px', maxWidth: '1000px', margin: '0 auto' }}>
      <div style={{ marginBottom: '20px' }}>
        <Link to="/requests" style={{ color: '#007bff', textDecoration: 'none' }}>
          ← Back to Pending Requests
        </Link>
      </div>

      <h1>Payment Request Review</h1>

      {error && (
        <div style={{ color: 'red', marginBottom: '15px', padding: '10px', backgroundColor: '#ffe6e6', borderRadius: '4px' }}>
          {error}
        </div>
      )}

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
                  Version {soa.versionNumber} — {soa.changeSummary || `Uploaded ${new Date(soa.uploadedAt).toLocaleString()}`}
                </div>
                {soa.downloadUrl && batchId && (
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

export default RequestDetailApprovalQueue
