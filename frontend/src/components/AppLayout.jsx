import { useState, useEffect } from 'react'
import { Outlet, useNavigate } from 'react-router-dom'
import { getCurrentUser, logout } from '../utils/auth'

/**
 * Shared layout for protected routes: header (Welcome, Logout) + outlet for page content.
 */
const AppLayout = () => {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)

  useEffect(() => {
    const load = async () => {
      try {
        const u = await getCurrentUser()
        setUser(u)
      } catch {
        setUser(null)
      }
    }
    load()
  }, [])

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 20px', borderBottom: '1px solid #eee', backgroundColor: '#fafafa' }}>
        <div />
        <div>
          {user && (
            <span style={{ marginRight: '15px' }}>
              Welcome, {user.displayName} ({user.role})
            </span>
          )}
          <button type="button" onClick={handleLogout} style={{ padding: '8px 16px', cursor: 'pointer' }}>
            Logout
          </button>
        </div>
      </header>
      <main style={{ flex: 1 }}>
        <Outlet />
      </main>
    </div>
  )
}

export default AppLayout
