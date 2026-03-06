// Extract a clean error message from API error responses
export const extractError = (error) => {
  if (error?.response?.data?.error?.message) {
    return error.response.data.error.message
  }
  if (error?.response?.data?.detail) {
    return error.response.data.detail
  }
  if (error?.message) {
    return error.message
  }
  return 'An unexpected error occurred.'
}

export const extractErrorCode = (error) =>
  error?.response?.data?.error?.code || null
