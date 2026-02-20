import api, { tokenStorage } from './api'

/**
 * Authentication utilities
 * Token handling follows SECURITY_MODEL.md
 */

export const login = async (username, password) => {
  const response = await api.post('/auth/login', { username, password })
  const { token, user } = response.data.data
  // Note: Refresh token may be included in response if backend supports it
  const refreshToken = response.data.data.refreshToken || response.data.data.refresh

  tokenStorage.setAccessToken(token)
  if (refreshToken) {
    tokenStorage.setRefreshToken(refreshToken)
  }

  return { user, token }
}

export const logout = async () => {
  try {
    await api.post('/auth/logout', {})
  } catch (error) {
    // Continue with logout even if API call fails
    console.error('Logout API call failed:', error)
  } finally {
    tokenStorage.clearTokens()
  }
}

export const getCurrentUser = async () => {
  const response = await api.get('/users/me')
  return response.data.data
}

export const isAuthenticated = () => {
  return !!tokenStorage.getAccessToken()
}
