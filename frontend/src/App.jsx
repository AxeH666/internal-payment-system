import { Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import RoleBasedRoute from './components/RoleBasedRoute'
import AppLayout from './components/AppLayout'
import Login from './pages/Login'
import { routeConfig } from './config/routes'

function App() {
  const homeRoute = routeConfig.find((r) => r.path === '/')
  const HomeComponent = homeRoute?.component
  const layoutRoutes = routeConfig.filter((r) => r.path !== '/')

  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route
        path="/"
        element={
          <ProtectedRoute>
            {HomeComponent && <HomeComponent />}
          </ProtectedRoute>
        }
      />

      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        {layoutRoutes.map(({ path, allowedRoles, component: Component }) => (
          <Route
            key={path}
            path={path.replace(/^\//, '')}
            element={
              allowedRoles ? (
                <RoleBasedRoute allowedRoles={allowedRoles}>
                  <Component />
                </RoleBasedRoute>
              ) : (
                <Component />
              )
            }
          />
        ))}
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
