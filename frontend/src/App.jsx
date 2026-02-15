import { Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import RoleBasedRoute from './components/RoleBasedRoute'
import Login from './pages/Login'
import Home from './pages/Home'
import BatchesList from './pages/BatchesList'
import CreateBatch from './pages/CreateBatch'
import BatchDetail from './pages/BatchDetail'
import RequestDetail from './pages/RequestDetail'
import PendingRequestsList from './pages/PendingRequestsList'
import RequestDetailApprovalQueue from './pages/RequestDetailApprovalQueue'
import AuditLog from './pages/AuditLog'

function App() {
  return (
    <Routes>
      {/* R1: Login - Unauthenticated only */}
      <Route path="/login" element={<Login />} />

      {/* R2: Home - Redirects based on role */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Home />
          </ProtectedRoute>
        }
      />

      {/* R3: Batches List */}
      <Route
        path="/batches"
        element={
          <ProtectedRoute>
            <RoleBasedRoute allowedRoles={['CREATOR', 'APPROVER', 'VIEWER']}>
              <BatchesList />
            </RoleBasedRoute>
          </ProtectedRoute>
        }
      />

      {/* R4: Create Batch - CREATOR only */}
      <Route
        path="/batches/new"
        element={
          <ProtectedRoute>
            <RoleBasedRoute allowedRoles={['CREATOR']}>
              <CreateBatch />
            </RoleBasedRoute>
          </ProtectedRoute>
        }
      />

      {/* R5: Batch Detail */}
      <Route
        path="/batches/:batchId"
        element={
          <ProtectedRoute>
            <RoleBasedRoute allowedRoles={['CREATOR', 'APPROVER', 'VIEWER']}>
              <BatchDetail />
            </RoleBasedRoute>
          </ProtectedRoute>
        }
      />

      {/* R6: Request Detail (from batch context) */}
      <Route
        path="/batches/:batchId/requests/:requestId"
        element={
          <ProtectedRoute>
            <RoleBasedRoute allowedRoles={['CREATOR', 'APPROVER', 'VIEWER']}>
              <RequestDetail />
            </RoleBasedRoute>
          </ProtectedRoute>
        }
      />

      {/* R7: Pending Requests List - APPROVER only */}
      <Route
        path="/requests"
        element={
          <ProtectedRoute>
            <RoleBasedRoute allowedRoles={['APPROVER']}>
              <PendingRequestsList />
            </RoleBasedRoute>
          </ProtectedRoute>
        }
      />

      {/* R8: Request Detail (from approval queue) - APPROVER only */}
      <Route
        path="/requests/:requestId"
        element={
          <ProtectedRoute>
            <RoleBasedRoute allowedRoles={['APPROVER']}>
              <RequestDetailApprovalQueue />
            </RoleBasedRoute>
          </ProtectedRoute>
        }
      />

      {/* R9: Audit Log */}
      <Route
        path="/audit"
        element={
          <ProtectedRoute>
            <RoleBasedRoute allowedRoles={['CREATOR', 'APPROVER', 'VIEWER']}>
              <AuditLog />
            </RoleBasedRoute>
          </ProtectedRoute>
        }
      />

      {/* Catch all - redirect to home */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
