import { useState, useEffect } from 'react'
import api, { unwrapPaginated } from '../utils/api'
import { extractError } from '../utils/errorHandler'
import {
  SectionHeader, ErrorBanner, SuccessBanner, LoadingSpinner,
  EmptyState, Pagination, ConfirmModal
} from '../components/ui'

const ROLES = ['CREATOR', 'APPROVER', 'VIEWER', 'ADMIN']

const ROLE_BADGE = {
  ADMIN:    'bg-accent/20 text-accent border border-accent/20',
  CREATOR:  'bg-success/20 text-success-text border border-success/20',
  APPROVER: 'bg-warning/20 text-warning-text border border-warning/20',
  VIEWER:   'bg-surface-muted text-text-secondary border border-surface-border',
}

const DEFAULT_FORM = { username: '', password: '', displayName: '', role: 'CREATOR' }

export default function UserManagement() {
  const [users, setUsers] = useState([])
  const [meta, setMeta] = useState({ total: 0, limit: 20, offset: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [form, setForm] = useState(DEFAULT_FORM)
  const [formError, setFormError] = useState('')
  const [creating, setCreating] = useState(false)

  useEffect(() => { loadUsers(0) }, [])

  const loadUsers = async (offset = 0) => {
    setLoading(true); setError('')
    try {
      const res = await api.get(`/users/?limit=20&offset=${offset}`)
      const { items, total } = unwrapPaginated(res)
      setUsers(items)
      setMeta({ total, limit: 20, offset })
    } catch (err) {
      setError(extractError(err))
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!form.username || !form.password || !form.displayName) {
      setFormError('All fields are required.'); return
    }
    setCreating(true); setFormError('')
    try {
      await api.post('/users/', form, {
        headers: { 'Idempotency-Key': `create-user-${form.username}-${Date.now()}` }
      })
      setSuccess(`User "${form.displayName}" created successfully.`)
      setShowModal(false)
      setForm(DEFAULT_FORM)
      loadUsers(0)
    } catch (err) {
      setFormError(extractError(err))
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="animate-fade-in">
      <SectionHeader
        title="User Management"
        subtitle={`${meta.total} user${meta.total !== 1 ? 's' : ''} in the system`}
        action={
          <button className="btn-primary" onClick={() => { setShowModal(true); setFormError('') }}>
            <span>+</span> Create User
          </button>
        }
      />

      <ErrorBanner message={error} onDismiss={() => setError('')} />
      <SuccessBanner message={success} onDismiss={() => setSuccess('')} />

      <div className="card overflow-hidden">
        {loading ? (
          <LoadingSpinner center />
        ) : users.length === 0 ? (
          <EmptyState
            title="No users yet"
            description="Create the first user account to get started."
            action={<button className="btn-primary" onClick={() => setShowModal(true)}>Create User</button>}
          />
        ) : (
          <>
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>User</th>
                    <th>Username</th>
                    <th>Role</th>
                    <th>ID</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(u => (
                    <tr key={u.id}>
                      <td>
                        <div className="flex items-center gap-2">
                          <div className="w-7 h-7 rounded-full bg-accent-muted flex items-center justify-center text-accent font-semibold text-xs flex-shrink-0">
                            {u.displayName?.[0]?.toUpperCase() || '?'}
                          </div>
                          <span className="text-text-primary font-medium">{u.displayName}</span>
                        </div>
                      </td>
                      <td className="font-mono text-xs">{u.username}</td>
                      <td>
                        <span className={`badge ${ROLE_BADGE[u.role] || ''}`}>{u.role}</span>
                      </td>
                      <td className="font-mono text-xs text-text-muted">{u.id?.slice(0, 8)}…</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination
              total={meta.total}
              limit={meta.limit}
              offset={meta.offset}
              onPageChange={loadUsers}
            />
          </>
        )}
      </div>

      {/* Create User Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-5">
              <div>
                <h3 className="text-text-primary font-semibold">Create User</h3>
                <p className="text-text-muted text-xs mt-0.5">Add a new user to the system</p>
              </div>
              <button className="btn-ghost btn-sm" onClick={() => setShowModal(false)}>✕</button>
            </div>

            <ErrorBanner message={formError} onDismiss={() => setFormError('')} />

            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label className="label">Display Name</label>
                <input className="input" placeholder="John Smith" value={form.displayName}
                  onChange={e => setForm(f => ({ ...f, displayName: e.target.value }))} autoFocus />
              </div>
              <div className="form-group">
                <label className="label">Username</label>
                <input className="input" placeholder="john.smith" value={form.username}
                  onChange={e => setForm(f => ({ ...f, username: e.target.value }))} autoComplete="off" />
              </div>
              <div className="form-group">
                <label className="label">Password</label>
                <input type="password" className="input" placeholder="Temporary password" value={form.password}
                  onChange={e => setForm(f => ({ ...f, password: e.target.value }))} autoComplete="new-password" />
              </div>
              <div className="form-group">
                <label className="label">Role</label>
                <select className="input" value={form.role}
                  onChange={e => setForm(f => ({ ...f, role: e.target.value }))}>
                  {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
                </select>
              </div>
              <div className="flex justify-end gap-3 mt-2">
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)} disabled={creating}>Cancel</button>
                <button type="submit" className="btn-primary" disabled={creating}>
                  {creating ? <><LoadingSpinner size="sm" /> Creating…</> : 'Create User'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
