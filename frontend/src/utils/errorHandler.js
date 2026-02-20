/**
 * Standardized error handling according to API contract
 * All API errors conform to: {"error": {"code": "...", "message": "...", "details": {}}}
 */

export const handleApiError = (error) => {
  if (error.response?.data?.error) {
    return {
      code: error.response.data.error.code,
      message: error.response.data.error.message,
      details: error.response.data.error.details || {},
      status: error.response.status,
    }
  }

  // Network or other errors
  return {
    code: 'NETWORK_ERROR',
    message: 'Network error. Please check your connection.',
    details: {},
    status: 0,
  }
}

export const handleErrorResponse = (error, navigate) => {
  const errorData = handleApiError(error)
  const { code, message, status } = errorData

  switch (status) {
    case 401:
      // UNAUTHORIZED: Clear token and redirect to login
      navigate('/login')
      return { message: 'Session expired. Please login again.' }

    case 403:
      // FORBIDDEN: Display permission message
      return { message: message || 'You do not have permission to perform this action.' }

    case 404:
      // NOT_FOUND: Display message with navigation option
      return { message: message || 'Resource not found.' }

    case 400:
      // VALIDATION_ERROR: Display validation message
      return { message: message || 'Validation error.', details: errorData.details }

    case 409:
      // CONFLICT or INVALID_STATE: Trigger reload behavior
      return {
        message: message || 'The operation could not complete due to a conflict. Please refresh and try again.',
        shouldReload: true,
      }

    case 412:
      // PRECONDITION_FAILED: Display message and reload
      return {
        message: message || 'Precondition failed. Please refresh and try again.',
        shouldReload: true,
      }

    case 500:
      // INTERNAL_ERROR: Display generic message
      return { message: 'An internal error occurred. Please try again later.' }

    default:
      return { message: message || 'An error occurred. Please try again.' }
  }
}
