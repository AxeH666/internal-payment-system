/**
 * Centralized route configuration.
 * Paths and allowedRoles must match backend permission model.
 */

import Home from '../pages/Home'
import BatchesList from '../pages/BatchesList'
import CreateBatch from '../pages/CreateBatch'
import BatchDetail from '../pages/BatchDetail'
import RequestDetail from '../pages/RequestDetail'
import PendingRequestsList from '../pages/PendingRequestsList'
import RequestDetailApprovalQueue from '../pages/RequestDetailApprovalQueue'
import AuditLog from '../pages/AuditLog'

export const routeConfig = [
  { path: '/', allowedRoles: null, component: Home },
  { path: '/batches', allowedRoles: ['CREATOR', 'APPROVER', 'VIEWER', 'ADMIN'], component: BatchesList },
  { path: '/batches/new', allowedRoles: ['CREATOR', 'ADMIN'], component: CreateBatch },
  { path: '/batches/:batchId', allowedRoles: ['CREATOR', 'APPROVER', 'VIEWER', 'ADMIN'], component: BatchDetail },
  { path: '/batches/:batchId/requests/:requestId', allowedRoles: ['CREATOR', 'APPROVER', 'VIEWER', 'ADMIN'], component: RequestDetail },
  { path: '/requests', allowedRoles: ['APPROVER', 'ADMIN'], component: PendingRequestsList },
  { path: '/requests/:requestId', allowedRoles: ['APPROVER', 'ADMIN'], component: RequestDetailApprovalQueue },
  { path: '/audit', allowedRoles: ['CREATOR', 'APPROVER', 'VIEWER', 'ADMIN'], component: AuditLog },
]
