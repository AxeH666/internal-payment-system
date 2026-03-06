import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api, { unwrapPaginated } from '../utils/api'
import { extractError } from '../utils/errorHandler'
import { getUser, ROLES } from '../utils/auth'
import {
  SectionHeader, StatusBadge, ErrorBanner, LoadingSpinner,
  EmptyState, Pagination
} from '../components/ui'

const STATUSES = ['', 'DRAFT', 'PROCESSING', 'COMPLETED', 'CANCELLED']

export default function BatchesList() {
  const navigate = useNavigate()
  const user = getUser()
  const canCreate = user?.role === ROLES.CREATOR || user?.role === ROLES.ADMIN

  const [batches, setBatches] = useState([])
  const [meta, setMeta] = useState({ total: 0, limit: 20, offset: 0 })
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => { loadBatches(0, statusFilter) }, [statusFilter])

  const loadBatches = async (offset = 0, status = '') => {
    setLoading(true); setError('')
    try {
      const params = new URLSearchParams({ limit: 20, offset })
      if (status) params.set('status', status)
      const res = await api.get(`/batches?${params}`)
      const { items, total } = unwrapPaginated(res)
      setBatches(items)
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
        title="Payment Batches"
        subtitle={`${meta.total} batch${meta.total !== 1 ? 'es' : ''} total`}
        action={canCreate && (
          <button className="btn-primary" onClick={() => navigate('/batches/new')}>
            <span>+</span> New Batch
          </button>
        )}
      />

      <ErrorBanner message={error} onDismiss={() => setError('')} />

      {/* Filter bar */}
      <div className="flex gap-2 mb-4 flex-wrap">
        {STATUSES.map(s => (
          <button
            key={s || 'all'}
            onClick={() => setStatusFilter(s)}
            className={`btn-sm rounded-full px-3 py-1 text-xs font-medium border transition-all ${
              statusFilter === s
                ? 'bg-accent text-white border-accent'
                : 'btn-secondary'
            }`}
          >
            {s || 'All'}
          </button>
        ))}
      </div>

      <div className="card overflow-hidden">
        {loading ? (
          <LoadingSpinner center />
        ) : batches.length === 0 ? (
          <EmptyState
            title="No batches found"
            description={statusFilter ? `No batches with status "${statusFilter}".` : 'Create your first payment batch to get started.'}
            action={canCreate && <button className="btn-primary" onClick={() => navigate('/batches/new')}>New Batch</button>}
          />
        ) : (
          <>
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Batch</th>
                    <th>Status</th>
                    <th>Requests</th>
                    <th>Created By</th>
                    <th>Created</th>
                    <th>Submitted</th>
                  </tr>
                </thead>
                <tbody>
                  {batches.map(b => (
                    <tr
                      key={b.id}
                      className="cursor-pointer"
                      onClick={() => navigate(`/batches/${b.id}`)}
                    >
                      <td className="primary">{b.title}</td>
                      <td><StatusBadge status={b.status} /></td>
                      <td>
                        <span className="text-text-primary font-medium">{b.requestCount ?? 0}</span>
                      </td>
                      <td className="text-text-muted">{b.createdBy}</td>
                      <td className="text-text-muted">{fmtDate(b.createdAt)}</td>
                      <td className="text-text-muted">{b.submittedAt ? fmtDate(b.submittedAt) : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination
              total={meta.total}
              limit={meta.limit}
              offset={meta.offset}
              onPageChange={(o) => loadBatches(o, statusFilter)}
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
