import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getUser, ROLES } from '../utils/auth'
import { StatCard, LoadingSpinner, ErrorBanner, StatusBadge } from '../components/ui'
import { extractError } from '../utils/errorHandler'
import api, { unwrapPaginated } from '../utils/api'

export default function Home() {
  const user = getUser()
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [recentBatches, setRecentBatches] = useState([])
  const [pendingCount, setPendingCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => { loadDashboard() }, [])

  const loadDashboard = async () => {
    setLoading(true); setError('')
    try {
      const [batchRes, requestRes] = await Promise.all([
        api.get('/batches?limit=5'),
        user.role !== ROLES.CREATOR
          ? api.get('/requests?status=PENDING_APPROVAL&limit=1')
          : Promise.resolve({ data: { results: [], count: 0 } }),
      ])

      const { items: batches, total } = unwrapPaginated(batchRes)
      const { total: pendingTotal } = unwrapPaginated(requestRes)

      setRecentBatches(batches)
      setPendingCount(pendingTotal)

      const draft = batches.filter(b => b.status === 'DRAFT').length
      const completed = batches.filter(b => b.status === 'COMPLETED').length
      setStats({ total, draft, completed })
    } catch (err) {
      setError(extractError(err))
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <LoadingSpinner center />

  return (
    <div className="animate-fade-in">
      {/* Welcome header */}
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-text-primary">
          Good {getTimeOfDay()},{' '}
          <span className="text-gradient">{user?.displayName?.split(' ')[0] || 'User'}</span>
        </h1>
        <p className="text-text-secondary text-sm mt-1">
          {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
        </p>
      </div>

      <ErrorBanner message={error} onDismiss={() => setError('')} />

      {/* Stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatCard label="Total Batches" value={stats?.total ?? '—'} accent />
        <StatCard label="Draft" value={stats?.draft ?? '—'} sub="Awaiting submission" />
        <StatCard label="Completed" value={stats?.completed ?? '—'} sub="Fully paid" />
        {user.role !== ROLES.CREATOR && (
          <StatCard
            label="Pending Approval"
            value={pendingCount}
            sub={pendingCount > 0 ? 'Requires attention' : 'All clear'}
            accent={pendingCount > 0}
          />
        )}
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {(user.role === ROLES.CREATOR || user.role === ROLES.ADMIN) && (
          <QuickAction
            icon="+"
            title="Create Batch"
            description="Start a new payment batch"
            onClick={() => navigate('/batches/new')}
            accent
          />
        )}
        {(user.role === ROLES.APPROVER || user.role === ROLES.ADMIN) && pendingCount > 0 && (
          <QuickAction
            icon="✓"
            title="Review Requests"
            description={`${pendingCount} request${pendingCount > 1 ? 's' : ''} awaiting approval`}
            onClick={() => navigate('/requests')}
            accent
          />
        )}
        {user.role === ROLES.ADMIN && (
          <QuickAction
            icon="⊕"
            title="Manage Users"
            description="Create and manage user accounts"
            onClick={() => navigate('/admin/users')}
          />
        )}
        <QuickAction
          icon="≡"
          title="View Batches"
          description="Browse all payment batches"
          onClick={() => navigate('/batches')}
        />
        <QuickAction
          icon="⟳"
          title="Audit Log"
          description="Review system activity"
          onClick={() => navigate('/audit')}
        />
      </div>

      {/* Recent batches */}
      {recentBatches.length > 0 && (
        <div className="card overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-surface-border">
            <span className="text-text-primary font-medium text-sm">Recent Batches</span>
            <button className="btn-ghost btn-sm" onClick={() => navigate('/batches')}>View all →</button>
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Status</th>
                  <th>Requests</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {recentBatches.map(b => (
                  <tr key={b.id} className="cursor-pointer" onClick={() => navigate(`/batches/${b.id}`)}>
                    <td className="primary">{b.title}</td>
                    <td><StatusBadge status={b.status} /></td>
                    <td>{b.requestCount ?? 0}</td>
                    <td>{formatDate(b.createdAt)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

function QuickAction({ icon, title, description, onClick, accent }) {
  return (
    <button
      onClick={onClick}
      className={`card p-4 text-left hover:shadow-elevated transition-all duration-150 group cursor-pointer w-full ${accent ? 'glow-border hover:bg-surface-raised' : 'hover:bg-surface-raised'}`}
    >
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold mb-3 ${accent ? 'bg-accent text-white' : 'bg-surface-muted text-text-secondary'}`}>
        {icon}
      </div>
      <div className="text-text-primary font-medium text-sm mb-0.5">{title}</div>
      <div className="text-text-muted text-xs">{description}</div>
    </button>
  )
}

function getTimeOfDay() {
  const h = new Date().getHours()
  if (h < 12) return 'morning'
  if (h < 17) return 'afternoon'
  return 'evening'
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
