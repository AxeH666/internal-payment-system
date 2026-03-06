import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../utils/api'
import { extractError } from '../utils/errorHandler'
import { getUser, ROLES } from '../utils/auth'
import { canApprove, canReject, canMarkPaid, canUploadSOA } from '../utils/stateVisibility'
import {
  StatusBadge, ErrorBanner, SuccessBanner, LoadingSpinner,
  ConfirmModal, SectionHeader
} from '../components/ui'

export default function RequestDetail() {
  const { batchId, requestId } = useParams()
  const navigate = useNavigate()
  const user = getUser()
  const fileRef = useRef()

  const [request, setRequest] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [comment, setComment] = useState('')
  const [approveModal, setApproveModal] = useState(false)
  const [rejectModal, setRejectModal] = useState(false)
  const [paidModal, setPaidModal] = useState(false)
  const [actionLoading, setActionLoading] = useState(false)
  const [uploading, setUploading] = useState(false)

  const isApprover = user?.role === ROLES.APPROVER
  const isAdmin = user?.role === ROLES.ADMIN

  useEffect(() => { loadRequest() }, [requestId])

  const loadRequest = async () => {
    setLoading(true); setError('')
    try {
      const url = batchId
        ? `/batches/${batchId}/requests/${requestId}`
        : `/requests/${requestId}`
      const res = await api.get(url)
      setRequest(res.data.data)
    } catch (err) {
      setError(extractError(err))
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async () => {
    setActionLoading(true)
    try {
      await api.post(`/requests/${requestId}/approve`, { comment }, {
        headers: { 'Idempotency-Key': `approve-${requestId}` }
      })
      setSuccess('Request approved.')
      setApproveModal(false); setComment('')
      loadRequest()
    } catch (err) { setError(extractError(err)); setApproveModal(false) }
    finally { setActionLoading(false) }
  }

  const handleReject = async () => {
    setActionLoading(true)
    try {
      await api.post(`/requests/${requestId}/reject`, { comment }, {
        headers: { 'Idempotency-Key': `reject-${requestId}` }
      })
      setSuccess('Request rejected.')
      setRejectModal(false); setComment('')
      loadRequest()
    } catch (err) { setError(extractError(err)); setRejectModal(false) }
    finally { setActionLoading(false) }
  }

  const handleMarkPaid = async () => {
    setActionLoading(true)
    try {
      await api.post(`/requests/${requestId}/mark-paid`, {}, {
        headers: { 'Idempotency-Key': `mark-paid-${requestId}` }
      })
      setSuccess('Request marked as paid.')
      setPaidModal(false)
      loadRequest()
    } catch (err) { setError(extractError(err)); setPaidModal(false) }
    finally { setActionLoading(false) }
  }

  const handleUploadSOA = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    setUploading(true)
    try {
      await api.post(`/batches/${batchId || request?.batchId}/requests/${requestId}/soa`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Idempotency-Key': `upload-soa-${requestId}-${Date.now()}`,
        },
      })
      setSuccess('SOA document uploaded.')
      loadRequest()
    } catch (err) {
      setError(extractError(err))
    } finally {
      setUploading(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  if (loading) return <LoadingSpinner center />
  if (!request && error) return (
    <div className="animate-fade-in">
      <ErrorBanner message={error} />
      <button className="btn-secondary mt-4" onClick={() => navigate(-1)}>← Go Back</button>
    </div>
  )

  const effectiveBatchId = batchId || request?.batchId

  return (
    <div className="animate-fade-in max-w-3xl">
      <SectionHeader
        title="Payment Request"
        subtitle={<StatusBadge status={request?.status} />}
        action={
          <div className="flex items-center gap-2">
            <button className="btn-ghost" onClick={() => navigate(-1)}>← Back</button>
            {canMarkPaid(request) && isAdmin && (
              <button className="btn-primary" onClick={() => setPaidModal(true)}>
                ✓ Mark as Paid
              </button>
            )}
            {canApprove(request) && (isApprover || isAdmin) && (
              <button className="btn-primary" onClick={() => setApproveModal(true)}>
                ✓ Approve
              </button>
            )}
            {canReject(request) && (isApprover || isAdmin) && (
              <button className="btn-danger" onClick={() => setRejectModal(true)}>
                ✗ Reject
              </button>
            )}
          </div>
        }
      />

      <ErrorBanner message={error} onDismiss={() => setError('')} />
      <SuccessBanner message={success} onDismiss={() => setSuccess('')} />

      {/* Main details */}
      <div className="card p-5 mb-4">
        <div className="grid grid-cols-2 gap-4">
          <InfoField label="Status" value={<StatusBadge status={request?.status} />} />
          <InfoField label="Currency" value={request?.currency || '—'} />

          {request?.entityType ? (
            <>
              <InfoField label="Entity Type" value={request.entityType} />
              <InfoField label="Entity" value={request.entityName || '—'} />
              <InfoField label="Site" value={request.siteCode || '—'} />
              <InfoField label="Base Amount" value={request.baseAmount ? `${request.baseAmount}` : '—'} />
              <InfoField label="Extra Amount" value={request.extraAmount ? `${request.extraAmount}` : '—'} />
              <InfoField label="Total Amount" value={
                <span className="text-text-primary font-semibold">{request.totalAmount || '—'}</span>
              } />
            </>
          ) : (
            <>
              <InfoField label="Beneficiary" value={request?.beneficiaryName || '—'} />
              <InfoField label="Account" value={<span className="font-mono text-xs">{request?.beneficiaryAccount || '—'}</span>} />
              <InfoField label="Amount" value={
                <span className="text-text-primary font-semibold">{request?.amount || '—'}</span>
              } />
              <InfoField label="Purpose" value={request?.purpose || '—'} />
            </>
          )}

          <InfoField label="Created" value={fmtDate(request?.createdAt)} />
          <InfoField label="Updated" value={request?.updatedAt ? fmtDate(request.updatedAt) : '—'} />
        </div>
      </div>

      {/* Approval record */}
      {request?.approval && (
        <div className={`card p-5 mb-4 border-l-4 ${request.approval.decision === 'APPROVED' ? 'border-l-success' : 'border-l-danger'}`}>
          <div className="text-xs font-semibold uppercase tracking-wide text-text-muted mb-3">Approval Record</div>
          <div className="grid grid-cols-2 gap-4">
            <InfoField label="Decision" value={<StatusBadge status={request.approval.decision} />} />
            <InfoField label="Approver" value={request.approval.approverId} />
            <InfoField label="Date" value={fmtDate(request.approval.createdAt)} />
            {request.approval.comment && (
              <InfoField label="Comment" value={request.approval.comment} />
            )}
          </div>
        </div>
      )}

      {/* SOA section */}
      <div className="card overflow-hidden mb-4">
        <div className="flex items-center justify-between px-4 py-3 border-b border-surface-border">
          <span className="text-text-primary font-medium text-sm">SOA Documents</span>
          {canUploadSOA(request) && (
            <label className={`btn-secondary btn-sm cursor-pointer ${uploading ? 'opacity-50 pointer-events-none' : ''}`}>
              {uploading ? <><LoadingSpinner size="sm" /> Uploading…</> : '↑ Upload SOA'}
              <input ref={fileRef} type="file" className="hidden" onChange={handleUploadSOA} />
            </label>
          )}
        </div>
        {!request?.soaVersions?.length ? (
          <div className="text-center py-8 text-text-muted text-sm">No SOA documents uploaded.</div>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr><th>Version</th><th>Uploaded</th><th>Source</th><th></th></tr>
              </thead>
              <tbody>
                {request.soaVersions.map(v => (
                  <tr key={v.id}>
                    <td className="primary font-mono">v{v.versionNumber}</td>
                    <td>{fmtDate(v.uploadedAt)}</td>
                    <td>{v.source || 'UPLOAD'}</td>
                    <td>
                      <a
                        href={`/api/v1/batches/${effectiveBatchId}/requests/${requestId}/soa/${v.id}/download`}
                        className="btn-ghost btn-sm text-accent"
                        target="_blank"
                        rel="noreferrer"
                      >
                        ↓ Download
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Approve modal */}
      {approveModal && (
        <div className="modal-overlay" onClick={() => setApproveModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h3 className="text-text-primary font-semibold mb-1">Approve Request</h3>
            <p className="text-text-muted text-sm mb-4">Add an optional comment before approving.</p>
            <div className="form-group">
              <label className="label">Comment (optional)</label>
              <textarea className="input resize-none" rows={3} value={comment}
                onChange={e => setComment(e.target.value)} placeholder="Approval notes…" />
            </div>
            <div className="flex justify-end gap-3 mt-2">
              <button className="btn-secondary" onClick={() => setApproveModal(false)} disabled={actionLoading}>Cancel</button>
              <button className="btn-primary" onClick={handleApprove} disabled={actionLoading}>
                {actionLoading ? <LoadingSpinner size="sm" /> : '✓ Confirm Approve'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Reject modal */}
      {rejectModal && (
        <div className="modal-overlay" onClick={() => setRejectModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h3 className="text-text-primary font-semibold mb-1">Reject Request</h3>
            <p className="text-text-muted text-sm mb-4">Add an optional comment before rejecting.</p>
            <div className="form-group">
              <label className="label">Comment (optional)</label>
              <textarea className="input resize-none" rows={3} value={comment}
                onChange={e => setComment(e.target.value)} placeholder="Reason for rejection…" />
            </div>
            <div className="flex justify-end gap-3 mt-2">
              <button className="btn-secondary" onClick={() => setRejectModal(false)} disabled={actionLoading}>Cancel</button>
              <button className="btn-danger" onClick={handleReject} disabled={actionLoading}>
                {actionLoading ? <LoadingSpinner size="sm" /> : '✗ Confirm Reject'}
              </button>
            </div>
          </div>
        </div>
      )}

      <ConfirmModal
        open={paidModal}
        title="Mark as Paid"
        message="Confirm this payment has been processed and mark the request as Paid."
        confirmLabel="Mark as Paid"
        variant="primary"
        onConfirm={handleMarkPaid}
        onCancel={() => setPaidModal(false)}
        loading={actionLoading}
      />
    </div>
  )
}

function InfoField({ label, value }) {
  return (
    <div>
      <div className="label">{label}</div>
      <div className="text-text-secondary text-sm">{value}</div>
    </div>
  )
}

function fmtDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
