import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api, { unwrapPaginated } from '../utils/api'
import { extractError } from '../utils/errorHandler'
import {
  SectionHeader, StatusBadge, ErrorBanner, LoadingSpinner,
  EmptyState, Pagination
} from '../components/ui'

const STATUSES = ['PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'PAID']

export default function PendingRequestsList() {
  const navigate = useNavigate()
  const [requests, setRequests] = useState([])
  const [meta, setMeta] = useState({ total: 0, limit: 20, offset: 0 })
  const [statusFilter, setStatusFilter] = useState('PENDING_APPROVAL')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => { loadRequests(0, statusFilter) }, [statusFilter])

  const loadRequests = async (offset = 0, status = 'PENDING_APPROVAL') => {
    setLoading(true); setError('')
    try {
      const res = await api.get(`/requests?status=${status}&limit=20&offset=${offset}`)
      const { items, total } = unwrapPaginated(res)
      setRequests(items)
      setMeta({ total, limit: 20, offset })
    } catch (err) {
      setError(extractError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="animate-fade-in">
      <SectionHeader
        title="Approval Queue"
        subtitle={`${meta.total} request${meta.total !== 1 ? 's' : ''}`}
      />

      <ErrorBanner message={error} onDismiss={() => setError('')} />

      {/* Status filter */}
      <div className="flex gap-2 mb-4 flex-wrap">
        {STATUSES.map(s => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`btn-sm rounded-full px-3 py-1 text-xs font-medium border transition-all ${
              statusFilter === s ? 'bg-accent text-white border-accent' : 'btn-secondary'
            }`}
          >
            {s.replace('_', ' ')}
          </button>
        ))}
      </div>

      <div className="card overflow-hidden">
        {loading ? (
          <LoadingSpinner center />
        ) : requests.length === 0 ? (
          <EmptyState
            title="No requests"
            description={`No requests with status "${statusFilter.replace('_', ' ')}".`}
          />
        ) : (
          <>
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Beneficiary / Entity</th>
                    <th>Batch</th>
                    <th>Amount</th>
                    <th>Currency</th>
                    <th>Status</th>
                    <th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {requests.map(r => (
                    <tr
                      key={r.id}
                      className="cursor-pointer"
                      onClick={() => navigate(`/requests/${r.id}`)}
                    >
                      <td className="primary">{r.entityName || r.beneficiaryName || '—'}</td>
                      <td className="text-text-muted text-xs">{r.batchTitle || '—'}</td>
                      <td className="font-mono text-text-primary">{r.amount || r.totalAmount || '—'}</td>
                      <td>{r.currency}</td>
                      <td><StatusBadge status={r.status} /></td>
                      <td className="text-text-muted">{fmtDate(r.createdAt)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination
              total={meta.total}
              limit={meta.limit}
              offset={meta.offset}
              onPageChange={(o) => loadRequests(o, statusFilter)}
            />
          </>
        )}
      </div>
    </div>
  )
}

function fmtDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
