import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../utils/api'
import { extractError } from '../utils/errorHandler'
import { getUser, ROLES } from '../utils/auth'
import { canSubmitBatch, canCancelBatch, canAddRequest } from '../utils/stateVisibility'
import {
  StatusBadge, ErrorBanner, SuccessBanner, LoadingSpinner,
  ConfirmModal, EmptyState, SectionHeader
} from '../components/ui'

export default function BatchDetail() {
  const { batchId } = useParams()
  const navigate = useNavigate()
  const user = getUser()

  const [batch, setBatch] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [submitModal, setSubmitModal] = useState(false)
  const [cancelModal, setCancelModal] = useState(false)
  const [actionLoading, setActionLoading] = useState(false)

  useEffect(() => { loadBatch() }, [batchId])

  const loadBatch = async () => {
    setLoading(true); setError('')
    try {
      const res = await api.get(`/batches/${batchId}`)
      setBatch(res.data.data)
    } catch (err) {
      setError(extractError(err))
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async () => {
    setActionLoading(true)
    try {
      await api.post(`/batches/${batchId}/submit`, {}, {
        headers: { 'Idempotency-Key': `submit-batch-${batchId}` }
      })
      setSuccess('Batch submitted for approval.')
      setSubmitModal(false)
      loadBatch()
    } catch (err) {
      setError(extractError(err))
      setSubmitModal(false)
    } finally {
      setActionLoading(false)
    }
  }

  const handleCancel = async () => {
    setActionLoading(true)
    try {
      await api.post(`/batches/${batchId}/cancel`, {}, {
        headers: { 'Idempotency-Key': `cancel-batch-${batchId}` }
      })
      setSuccess('Batch cancelled.')
      setCancelModal(false)
      loadBatch()
    } catch (err) {
      setError(extractError(err))
      setCancelModal(false)
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) return <LoadingSpinner center />

  const isOwnerOrAdmin = user?.role === ROLES.ADMIN || batch?.createdBy === user?.id

  return (
    <div className="animate-fade-in">
      <SectionHeader
        title={batch?.title || 'Batch Detail'}
        subtitle={`${batch?.requests?.length ?? 0} request${batch?.requests?.length !== 1 ? 's' : ''}`}
        action={
          <div className="flex items-center gap-2">
            <button className="btn-ghost" onClick={() => navigate('/batches')}>← Back</button>
            {canAddRequest(batch) && isOwnerOrAdmin && (
              <button className="btn-secondary" onClick={() => navigate(`/batches/${batchId}/requests/new`)}>
                + Add Request
              </button>
            )}
            {canSubmitBatch(batch) && isOwnerOrAdmin && (
              <button className="btn-primary" onClick={() => setSubmitModal(true)}>
                Submit Batch
              </button>
            )}
            {canCancelBatch(batch) && isOwnerOrAdmin && (
              <button className="btn-danger" onClick={() => setCancelModal(true)}>
                Cancel
              </button>
            )}
          </div>
        }
      />

      <ErrorBanner message={error} onDismiss={() => setError('')} />
      <SuccessBanner message={success} onDismiss={() => setSuccess('')} />

      {/* Batch info card */}
      <div className="card p-5 mb-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <InfoField label="Status" value={<StatusBadge status={batch?.status} />} />
          <InfoField label="Created" value={fmtDate(batch?.createdAt)} />
          <InfoField label="Submitted" value={batch?.submittedAt ? fmtDate(batch.submittedAt) : '—'} />
          <InfoField label="Completed" value={batch?.completedAt ? fmtDate(batch.completedAt) : '—'} />
        </div>
      </div>

      {/* Requests table */}
      <div className="card overflow-hidden">
        <div className="px-4 py-3 border-b border-surface-border">
          <span className="text-text-primary font-medium text-sm">Payment Requests</span>
        </div>
        {!batch?.requests?.length ? (
          <EmptyState
            title="No requests yet"
            description="Add payment requests to this batch."
            action={canAddRequest(batch) && isOwnerOrAdmin && (
              <button className="btn-primary" onClick={() => navigate(`/batches/${batchId}/requests/new`)}>
                Add Request
              </button>
            )}
          />
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Beneficiary / Entity</th>
                  <th>Amount</th>
                  <th>Currency</th>
                  <th>Status</th>
                  <th>SOA</th>
                </tr>
              </thead>
              <tbody>
                {batch.requests.map(r => (
                  <tr
                    key={r.id}
                    className="cursor-pointer"
                    onClick={() => navigate(`/batches/${batchId}/requests/${r.id}`)}
                  >
                    <td className="primary">
                      {r.entityName || r.beneficiaryName || '—'}
                      {r.siteCode && <span className="ml-2 text-text-muted text-xs">{r.siteCode}</span>}
                    </td>
                    <td className="font-mono text-text-primary">
                      {r.totalAmount || r.amount || '—'}
                    </td>
                    <td>{r.currency}</td>
                    <td><StatusBadge status={r.status} /></td>
                    <td className="text-text-muted text-xs">
                      {r.soaVersions?.length > 0 ? `v${r.soaVersions.length}` : 'None'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <ConfirmModal
        open={submitModal}
        title="Submit Batch"
        message={`Submit "${batch?.title}" for approval? All ${batch?.requests?.length} request(s) will move to Pending Approval.`}
        confirmLabel="Submit"
        variant="primary"
        onConfirm={handleSubmit}
        onCancel={() => setSubmitModal(false)}
        loading={actionLoading}
      />
      <ConfirmModal
        open={cancelModal}
        title="Cancel Batch"
        message={`Are you sure you want to cancel "${batch?.title}"? This action cannot be undone.`}
        confirmLabel="Cancel Batch"
        variant="danger"
        onConfirm={handleCancel}
        onCancel={() => setCancelModal(false)}
        loading={actionLoading}
      />
    </div>
  )
}

function InfoField({ label, value }) {
  return (
    <div>
      <div className="label">{label}</div>
      <div className="text-text-primary text-sm">{value}</div>
    </div>
  )
}

function fmtDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
