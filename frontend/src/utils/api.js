import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Token storage utilities
export const tokenStorage = {
  getAccessToken: () => {
    return localStorage.getItem('accessToken')
  },
  setAccessToken: (token) => {
    localStorage.setItem('accessToken', token)
  },
  getRefreshToken: () => {
    return localStorage.getItem('refreshToken')
  },
  setRefreshToken: (token) => {
    localStorage.setItem('refreshToken', token)
  },
  clearTokens: () => {
    localStorage.removeItem('accessToken')
    localStorage.removeItem('refreshToken')
  },
}

// Request interceptor: attach token
api.interceptors.request.use(
  (config) => {
    const token = tokenStorage.getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor: handle 401 and refresh token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const refreshToken = tokenStorage.getRefreshToken()
      if (refreshToken) {
        try {
          // Try refresh endpoint - format may vary by backend implementation
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh: refreshToken,
          })
          const access = response.data.data?.access || response.data.access || response.data.data?.token || response.data.token
          if (access) {
            tokenStorage.setAccessToken(access)
            const newRefresh = response.data.data?.refresh || response.data.refresh
            if (newRefresh) {
              tokenStorage.setRefreshToken(newRefresh)
            }
            originalRequest.headers.Authorization = `Bearer ${access}`
            return api(originalRequest)
          }
        } catch (refreshError) {
          // Refresh failed - clear tokens and redirect to login
          tokenStorage.clearTokens()
          window.location.href = '/login'
          return Promise.reject(refreshError)
        }
      }
      // No refresh token available - clear and redirect
      tokenStorage.clearTokens()
      window.location.href = '/login'
    }

    return Promise.reject(error)
  }
)

export default api
