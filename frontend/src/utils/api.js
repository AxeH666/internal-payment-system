import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Handle 401 → redirect to login
// Handle 409 → reload page (server state changed)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    if (error.response?.status === 409) {
      window.location.reload()
    }
    return Promise.reject(error)
  }
)

// Helper to normalize paginated responses:
// - API-style:   { data: [...], meta: { total } }
// - DRF-style:   { results: [...], count }
export const unwrapPaginated = (response) => {
  const payload = response?.data || {}
  const items = payload.data ?? payload.results ?? []
  const total =
    payload.meta?.total ??
    payload.count ??
    (Array.isArray(items) ? items.length : 0)

  return { items, total, raw: payload }
}

export default api
