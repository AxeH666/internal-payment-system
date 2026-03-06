import { useState } from 'react'
import { NavLink, useNavigate, Outlet } from 'react-router-dom'
import { getUser, clearAuth, ROLES } from '../utils/auth'
import api from '../utils/api'

const NAV = {
  [ROLES.ADMIN]: [
    { to: '/',              icon: GridIcon,    label: 'Dashboard'       },
    { to: '/admin/users',   icon: UsersIcon,   label: 'Users'           },
    { to: '/batches',       icon: LayersIcon,  label: 'Batches'         },
    { to: '/requests',      icon: CheckIcon,   label: 'Approval Queue'  },
    { to: '/audit',         icon: ClockIcon,   label: 'Audit Log'       },
  ],
  [ROLES.CREATOR]: [
    { to: '/',              icon: GridIcon,    label: 'Dashboard'       },
    { to: '/batches',       icon: LayersIcon,  label: 'My Batches'      },
    { to: '/audit',         icon: ClockIcon,   label: 'Audit Log'       },
  ],
  [ROLES.APPROVER]: [
    { to: '/',              icon: GridIcon,    label: 'Dashboard'       },
    { to: '/requests',      icon: CheckIcon,   label: 'Approval Queue'  },
    { to: '/batches',       icon: LayersIcon,  label: 'Batches'         },
    { to: '/audit',         icon: ClockIcon,   label: 'Audit Log'       },
  ],
  [ROLES.VIEWER]: [
    { to: '/',              icon: GridIcon,    label: 'Dashboard'       },
    { to: '/batches',       icon: LayersIcon,  label: 'Batches'         },
    { to: '/audit',         icon: ClockIcon,   label: 'Audit Log'       },
  ],
}

const ROLE_BADGE = {
  ADMIN:    'bg-accent/20 text-accent',
  CREATOR:  'bg-success/20 text-success-text',
  APPROVER: 'bg-warning/20 text-warning-text',
  VIEWER:   'bg-surface-muted text-text-secondary',
}

export default function AppLayout() {
  const user = getUser()
  const navigate = useNavigate()
  const [loggingOut, setLoggingOut] = useState(false)
  const [collapsed, setCollapsed] = useState(false)

  const links = NAV[user?.role] || NAV[ROLES.VIEWER]

  const handleLogout = async () => {
    setLoggingOut(true)
    try { await api.post('/auth/logout', {}) } catch { /* ignore */ }
    clearAuth()
    navigate('/login')
  }

  return (
    <div className="flex h-screen bg-base-900 overflow-hidden">
      {/* Sidebar */}
      <aside className={`flex flex-col bg-base-800 border-r border-surface-border transition-all duration-200 ${collapsed ? 'w-16' : 'w-56'} flex-shrink-0`}>
        {/* Logo */}
        <div className={`flex items-center gap-3 px-4 py-5 border-b border-surface-border ${collapsed ? 'justify-center px-0' : ''}`}>
          <div className="w-7 h-7 rounded-lg bg-accent flex items-center justify-center flex-shrink-0">
            <span className="text-white font-bold text-xs">IP</span>
          </div>
          {!collapsed && (
            <div>
              <div className="text-text-primary font-semibold text-sm leading-tight">InternalPay</div>
              <div className="text-text-muted text-xs">Workflow System</div>
            </div>
          )}
        </div>

        {/* Nav links */}
        <nav className="flex-1 p-3 flex flex-col gap-1 overflow-y-auto scrollbar-none">
          {links.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `sidebar-link ${isActive ? 'active' : ''} ${collapsed ? 'justify-center px-0' : ''}`
              }
            >
              <Icon size={16} className="flex-shrink-0" />
              {!collapsed && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* User + Logout */}
        <div className="p-3 border-t border-surface-border">
          {!collapsed && (
            <div className="flex items-center gap-2 px-2 py-2 mb-2 rounded-lg bg-surface/50">
              <div className="w-7 h-7 rounded-full bg-accent-muted flex items-center justify-center text-accent font-semibold text-xs flex-shrink-0">
                {user?.displayName?.[0]?.toUpperCase() || 'U'}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-text-primary text-xs font-medium truncate">{user?.displayName}</div>
                <span className={`inline-block text-xs px-1.5 py-0.5 rounded font-medium ${ROLE_BADGE[user?.role] || ''}`}>
                  {user?.role}
                </span>
              </div>
            </div>
          )}
          <button
            onClick={handleLogout}
            disabled={loggingOut}
            className={`sidebar-link w-full text-danger hover:bg-danger/10 hover:text-danger ${collapsed ? 'justify-center px-0' : ''}`}
          >
            <LogoutIcon size={16} />
            {!collapsed && <span>{loggingOut ? 'Signing out…' : 'Sign Out'}</span>}
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Topbar */}
        <header className="h-14 bg-base-800 border-b border-surface-border flex items-center px-6 gap-4 flex-shrink-0">
          <button
            onClick={() => setCollapsed(c => !c)}
            className="btn-ghost btn-sm text-text-muted"
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            <MenuIcon size={16} />
          </button>
          <div className="flex-1" />
          <div className="flex items-center gap-2 text-text-secondary text-xs">
            <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
            Connected
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-6 animate-fade-in">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

// Inline icon components (no extra dep)
function GridIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
      <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
    </svg>
  )
}
function UsersIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
      <circle cx="9" cy="7" r="4"/>
      <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
      <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
    </svg>
  )
}
function LayersIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
      <polygon points="12 2 2 7 12 12 22 7 12 2"/>
      <polyline points="2 17 12 22 22 17"/>
      <polyline points="2 12 12 17 22 12"/>
    </svg>
  )
}
function CheckIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
      <polyline points="9 11 12 14 22 4"/>
      <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
    </svg>
  )
}
function ClockIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <polyline points="12 6 12 12 16 14"/>
    </svg>
  )
}
function LogoutIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
      <polyline points="16 17 21 12 16 7"/>
      <line x1="21" y1="12" x2="9" y2="12"/>
    </svg>
  )
}
function MenuIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
      <line x1="3" y1="6" x2="21" y2="6"/>
      <line x1="3" y1="12" x2="21" y2="12"/>
      <line x1="3" y1="18" x2="21" y2="18"/>
    </svg>
  )
}
