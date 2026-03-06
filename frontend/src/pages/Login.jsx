import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { setAuth, isAuthenticated } from '../utils/auth'
import { extractError } from '../utils/errorHandler'
import { ErrorBanner, LoadingSpinner } from '../components/ui'
import api from '../utils/api'

export default function Login() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ username: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (isAuthenticated()) { navigate('/'); return null }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.username || !form.password) { setError('Username and password are required.'); return }
    setLoading(true); setError('')
    try {
      const res = await api.post('/auth/login', form)
      setAuth(res.data.data.token, res.data.data.user)
      navigate('/')
    } catch (err) {
      setError(extractError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-base-900 flex items-center justify-center p-4">
      {/* Background grid decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute inset-0" style={{backgroundImage:'radial-gradient(circle at 1px 1px, rgba(99,102,241,0.06) 1px, transparent 0)', backgroundSize:'32px 32px'}} />
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-accent/5 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-accent mb-4 shadow-glow">
            <span className="text-white font-bold text-lg">IP</span>
          </div>
          <h1 className="text-text-primary text-xl font-semibold">InternalPay</h1>
          <p className="text-text-secondary text-sm mt-1">Internal Payment Workflow System</p>
        </div>

        {/* Card */}
        <div className="card p-6">
          <h2 className="text-text-primary font-semibold mb-1">Sign in</h2>
          <p className="text-text-muted text-xs mb-5">Enter your credentials to access the system</p>

          <ErrorBanner message={error} onDismiss={() => setError('')} />

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="form-group">
              <label className="label">Username</label>
              <input
                type="text"
                className="input"
                placeholder="your.username"
                value={form.username}
                onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
                autoComplete="username"
                autoFocus
              />
            </div>
            <div className="form-group">
              <label className="label">Password</label>
              <input
                type="password"
                className="input"
                placeholder="••••••••"
                value={form.password}
                onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                autoComplete="current-password"
              />
            </div>
            <button type="submit" className="btn-primary w-full justify-center mt-2" disabled={loading}>
              {loading ? <><LoadingSpinner size="sm" /> Signing in…</> : 'Sign In'}
            </button>
          </form>
        </div>

        <p className="text-center text-text-muted text-xs mt-6">
          Access is restricted to authorized personnel only.
        </p>
      </div>
    </div>
  )
}
