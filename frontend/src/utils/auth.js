export const getToken = () => localStorage.getItem('access_token')
export const getUser = () => {
  try {
    return JSON.parse(localStorage.getItem('user') || 'null')
  } catch {
    return null
  }
}

export const setAuth = (token, user) => {
  localStorage.setItem('access_token', token)
  localStorage.setItem('user', JSON.stringify(user))
}

export const clearAuth = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user')
}

export const isAuthenticated = () => !!getToken()
export const getRole = () => getUser()?.role || null

export const ROLES = {
  ADMIN: 'ADMIN',
  CREATOR: 'CREATOR',
  APPROVER: 'APPROVER',
  VIEWER: 'VIEWER',
}
