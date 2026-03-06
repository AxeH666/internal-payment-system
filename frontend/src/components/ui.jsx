import { STATUS_BADGE_CLASS, STATUS_LABELS } from '../utils/stateVisibility'

// ── Status Badge ─────────────────────────────────────────────────────────────
export function StatusBadge({ status }) {
  return (
    <span className={STATUS_BADGE_CLASS[status] || 'badge'}>
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-70" />
      {STATUS_LABELS[status] || status}
    </span>
  )
}

// ── Error Banner ─────────────────────────────────────────────────────────────
export function ErrorBanner({ message, onDismiss }) {
  if (!message) return null
  return (
    <div className="flex items-start gap-3 p-4 rounded-lg bg-danger/10 border border-danger/30 mb-4 animate-slide-in">
      <span className="text-danger mt-0.5">
        <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
          <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
      </span>
      <span className="flex-1 text-danger-text text-sm">{message}</span>
      {onDismiss && (
        <button onClick={onDismiss} className="text-danger/60 hover:text-danger transition-colors">
          <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      )}
    </div>
  )
}

// ── Success Banner ────────────────────────────────────────────────────────────
export function SuccessBanner({ message, onDismiss }) {
  if (!message) return null
  return (
    <div className="flex items-start gap-3 p-4 rounded-lg bg-success/10 border border-success/30 mb-4 animate-slide-in">
      <span className="text-success mt-0.5">
        <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
          <polyline points="20 6 9 17 4 12"/>
        </svg>
      </span>
      <span className="flex-1 text-success-text text-sm">{message}</span>
      {onDismiss && (
        <button onClick={onDismiss} className="text-success/60 hover:text-success transition-colors">
          <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      )}
    </div>
  )
}

// ── Loading Spinner ───────────────────────────────────────────────────────────
export function LoadingSpinner({ size = 'md', center = false }) {
  const s = { sm: 'w-4 h-4', md: 'w-6 h-6', lg: 'w-10 h-10' }[size]
  return (
    <div className={center ? 'flex justify-center items-center py-16' : 'inline-flex'}>
      <svg className={`${s} animate-spin text-accent`} viewBox="0 0 24 24" fill="none">
        <circle className="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3"/>
        <path className="opacity-80" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
      </svg>
    </div>
  )
}

// ── Confirm Modal ─────────────────────────────────────────────────────────────
export function ConfirmModal({ open, title, message, confirmLabel = 'Confirm', variant = 'danger', onConfirm, onCancel, loading }) {
  if (!open) return null
  const btnClass = variant === 'danger' ? 'btn-danger' : 'btn-primary'
  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <h3 className="text-text-primary font-semibold text-base mb-2">{title}</h3>
        <p className="text-text-secondary text-sm mb-6">{message}</p>
        <div className="flex justify-end gap-3">
          <button className="btn-secondary" onClick={onCancel} disabled={loading}>Cancel</button>
          <button className={btnClass} onClick={onConfirm} disabled={loading}>
            {loading ? <LoadingSpinner size="sm" /> : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Empty State ───────────────────────────────────────────────────────────────
export function EmptyState({ icon, title, description, action }) {
  return (
    <div className="empty-state">
      {icon && <div className="text-text-muted mb-4">{icon}</div>}
      <h3 className="text-text-primary font-medium mb-1">{title}</h3>
      {description && <p className="text-text-secondary text-sm mb-4 max-w-sm">{description}</p>}
      {action}
    </div>
  )
}

// ── Pagination ────────────────────────────────────────────────────────────────
export function Pagination({ total, limit, offset, onPageChange }) {
  const page = Math.floor(offset / limit)
  const totalPages = Math.ceil(total / limit)
  if (totalPages <= 1) return null
  return (
    <div className="flex items-center justify-between px-4 py-3 border-t border-surface-border">
      <span className="text-text-muted text-xs">
        {offset + 1}–{Math.min(offset + limit, total)} of {total}
      </span>
      <div className="flex items-center gap-2">
        <button
          className="btn-secondary btn-sm"
          disabled={page === 0}
          onClick={() => onPageChange((page - 1) * limit)}
        >← Prev</button>
        <span className="text-text-secondary text-xs">{page + 1} / {totalPages}</span>
        <button
          className="btn-secondary btn-sm"
          disabled={page >= totalPages - 1}
          onClick={() => onPageChange((page + 1) * limit)}
        >Next →</button>
      </div>
    </div>
  )
}

// ── Section Header ────────────────────────────────────────────────────────────
export function SectionHeader({ title, subtitle, action }) {
  return (
    <div className="page-header">
      <div>
        <h1 className="page-title">{title}</h1>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </div>
      {action}
    </div>
  )
}

// ── Stat Card ─────────────────────────────────────────────────────────────────
export function StatCard({ label, value, sub, accent }) {
  return (
    <div className={`stat-card ${accent ? 'glow-border' : ''}`}>
      <div className="text-text-muted text-xs font-medium uppercase tracking-wide">{label}</div>
      <div className={`text-3xl font-bold ${accent ? 'text-gradient' : 'text-text-primary'}`}>{value}</div>
      {sub && <div className="text-text-muted text-xs">{sub}</div>}
    </div>
  )
}
