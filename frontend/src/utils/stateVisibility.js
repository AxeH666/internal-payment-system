// All visibility decisions are based on server-provided state.
// No business logic lives here — only mapping state to UI visibility.

export const canSubmitBatch = (batch) =>
  batch?.status === 'DRAFT' && (batch?.requestCount ?? 0) > 0

export const canCancelBatch = (batch) => batch?.status === 'DRAFT'

export const canAddRequest = (batch) => batch?.status === 'DRAFT'

export const canEditRequest = (request) => request?.status === 'DRAFT'

export const canApprove = (request) => request?.status === 'PENDING_APPROVAL'

export const canReject = (request) => request?.status === 'PENDING_APPROVAL'

export const canMarkPaid = (request) => request?.status === 'APPROVED'

export const canUploadSOA = (request) => request?.status === 'DRAFT'

export const STATUS_LABELS = {
  DRAFT: 'Draft',
  SUBMITTED: 'Submitted',
  PROCESSING: 'Processing',
  COMPLETED: 'Completed',
  CANCELLED: 'Cancelled',
  PENDING_APPROVAL: 'Pending Approval',
  APPROVED: 'Approved',
  REJECTED: 'Rejected',
  PAID: 'Paid',
}

export const STATUS_BADGE_CLASS = {
  DRAFT: 'badge-draft',
  SUBMITTED: 'badge-submitted',
  PROCESSING: 'badge-processing',
  COMPLETED: 'badge-completed',
  CANCELLED: 'badge-cancelled',
  PENDING_APPROVAL: 'badge-pending',
  APPROVED: 'badge-approved',
  REJECTED: 'badge-rejected',
  PAID: 'badge-paid',
}
