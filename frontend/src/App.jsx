import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { isAuthenticated, getRole, ROLES } from './utils/auth'

import AppLayout from './components/AppLayout'
import { ProtectedRoute, RoleBasedRoute } from './components/ProtectedRoute'

import Login from './pages/Login'
import Home from './pages/Home'
import UserManagement from './pages/UserManagement'
import BatchesList from './pages/BatchesList'
import CreateBatch from './pages/CreateBatch'
import BatchDetail from './pages/BatchDetail'
import RequestDetail from './pages/RequestDetail'
import PendingRequestsList from './pages/PendingRequestsList'
import AuditLog from './pages/AuditLog'
import NexusShell from './pages/NexusShell'

function RoleHome() {
  if (!isAuthenticated()) return <Navigate to="/login" replace />
  return <Navigate to="/" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public */}
        <Route path="/login" element={<Login />} />

        {/* Protected — all authenticated users */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Home />} />
          <Route path="batches" element={<BatchesList />} />
          <Route path="batches/new" element={
            <RoleBasedRoute roles={[ROLES.CREATOR, ROLES.ADMIN]}>
              <CreateBatch />
            </RoleBasedRoute>
          } />
          <Route path="batches/:batchId" element={<BatchDetail />} />
          <Route path="batches/:batchId/requests/:requestId" element={<RequestDetail />} />

          {/* Standalone request detail (from approval queue) */}
          <Route path="requests" element={
            <RoleBasedRoute roles={[ROLES.APPROVER, ROLES.ADMIN]}>
              <PendingRequestsList />
            </RoleBasedRoute>
          } />
          <Route path="requests/:requestId" element={
            <RoleBasedRoute roles={[ROLES.APPROVER, ROLES.ADMIN]}>
              <RequestDetail />
            </RoleBasedRoute>
          } />

          {/* Admin only */}
          <Route path="admin/users" element={
            <RoleBasedRoute roles={[ROLES.ADMIN]}>
              <UserManagement />
            </RoleBasedRoute>
          } />

          <Route path="audit" element={<AuditLog />} />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>

        {/* Nexus shell showcase (protected, admin only) */}
        <Route
          path="/shell"
          element={
            <RoleBasedRoute roles={[ROLES.ADMIN]}>
              <NexusShell />
            </RoleBasedRoute>
          }
        />

        {/* Root fallback */}
        <Route path="*" element={<RoleHome />} />
      </Routes>
    </BrowserRouter>
  )
}
