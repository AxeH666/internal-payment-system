import { useState, useEffect } from 'react'
import api, { unwrapPaginated } from '../utils/api'
import { extractError } from '../utils/errorHandler'
import { SectionHeader, ErrorBanner, LoadingSpinner, EmptyState, Pagination } from '../components/ui'

const EVENT_COLORS = {
  BATCH_CREATED:      'text-info',
  BATCH_SUBMITTED:    'text-info',
  BATCH_CANCELLED:    'text-danger',
  BATCH_COMPLETED:    'text-success',
  REQUEST_CREATED:    'text-info',
  REQUEST_APPROVED:   'text-success',
  REQUEST_REJECTED:   'text-danger',
  REQUEST_PAID:       'text-accent',
  SOA_UPLOADED:       'text-warning-text',
  SOA_DOWNLOADED:     'text-text-secondary',
  USER_CREATED:       'text-success',
}

export default function AuditLog() {
  const [logs, setLogs] = useState([])
  const [meta, setMeta] = useState({ total: 0, limit: 50, offset: 0 })
  const [filters, setFilters] = useState({ entityType: '', actorId: '', fromDate: '', toDate: '' })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => { loadLogs(0) }, [filters])

  const loadLogs = async (offset = 0) => {
    setLoading(true); setError('')
    try {
      const params = new URLSearchParams({ limit: 50, offset })
      if (filters.entityType) params.set('entityType', filters.entityType)
      if (filters.actorId) params.set('actorId', filters.actorId)
      if (filters.fromDate) params.set('fromDate', filters.fromDate)
      if (filters.toDate) params.set('toDate', filters.toDate)
      const res = await api.get(`/audit?${params}`)
      const { items, total } = unwrapPaginated(res)
      setLogs(items)
      setMeta({ total, limit: 50, offset })
    } catch (err) {
      setError(extractError(err))
    } finally {
      setLoading(false)
    }
  }

  const clearFilters = () => setFilters({ entityType: '', actorId: '', fromDate: '', toDate: '' })

  return (
    <div className="animate-fade-in">
      <SectionHeader
        title="Audit Log"
        subtitle={`${meta.total} event${meta.total !== 1 ? 's' : ''} recorded`}
        action={
          <button className="btn-ghost btn-sm" onClick={clearFilters}>Clear Filters</button>
        }
      />

      <ErrorBanner message={error} onDismiss={() => setError('')} />

      {/* Filters */}
      <div className="card p-4 mb-4 grid grid-cols-2 md:grid-cols-4 gap-3">
        <div>
          <label className="label">Entity Type</label>
          <select className="input" value={filters.entityType}
            onChange={e => setFilters(f => ({ ...f, entityType: e.target.value }))}>
            <option value="">All</option>
            <option>PaymentBatch</option>
            <option>PaymentRequest</option>
            <option>Client</option>
            <option>Site</option>
            <option>Vendor</option>
            <option>Subcontractor</option>
            <option>SOAVersion</option>
          </select>
        </div>
        <div>
          <label className="label">From Date</label>
          <input type="date" className="input" value={filters.fromDate}
            onChange={e => setFilters(f => ({ ...f, fromDate: e.target.value }))} />
        </div>
        <div>
          <label className="label">To Date</label>
          <input type="date" className="input" value={filters.toDate}
            onChange={e => setFilters(f => ({ ...f, toDate: e.target.value }))} />
        </div>
        <div>
          <label className="label">Actor ID</label>
          <input className="input font-mono text-xs" placeholder="User UUID…" value={filters.actorId}
            onChange={e => setFilters(f => ({ ...f, actorId: e.target.value }))} />
        </div>
      </div>

      <div className="card overflow-hidden">
        {loading ? (
          <LoadingSpinner center />
        ) : logs.length === 0 ? (
          <EmptyState title="No audit events" description="No events match your filters." />
        ) : (
          <>
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Event</th>
                    <th>Entity Type</th>
                    <th>Entity ID</th>
                    <th>Actor</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map(log => (
                    <tr key={log.id}>
                      <td>
                        <span className={`font-mono text-xs font-medium ${EVENT_COLORS[log.eventType] || 'text-text-secondary'}`}>
                          {log.eventType}
                        </span>
                      </td>
                      <td className="text-text-muted text-xs">{log.entityType}</td>
                      <td className="font-mono text-xs text-text-muted">{log.entityId?.slice(0, 8)}…</td>
                      <td className="font-mono text-xs text-text-muted">{log.actorId?.slice(0, 8)}…</td>
                      <td className="text-text-muted text-xs">{fmtDateTime(log.occurredAt)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination
              total={meta.total}
              limit={meta.limit}
              offset={meta.offset}
              onPageChange={loadLogs}
            />
          </>
        )}
      </div>
    </div>
  )
}

function fmtDateTime(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
  })
}
