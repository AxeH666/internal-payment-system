/**
 * State-Based UI Visibility Rules
 * These functions determine button visibility based on backend state only.
 * No business logic - purely rendering rules based on server state.
 */

/**
 * Batch-level visibility rules
 * Returns which buttons should be visible based on batch status and user role
 */
export const getBatchActionVisibility = (batch, currentUser) => {
  const isCreator = currentUser?.role === 'CREATOR'
  const isBatchCreator = batch?.createdBy === currentUser?.id
  const isDraft = batch?.status === 'DRAFT'
  const isClosed = batch?.status === 'COMPLETED' || batch?.status === 'CANCELLED'

  // CLOSED batch rule: all mutation actions disabled
  if (isClosed) {
    return {
      submitButton: false,
      cancelButton: false,
      addRequestButton: false,
    }
  }

  // DRAFT state: buttons visible only to CREATOR who is batch creator
  if (isDraft && isCreator && isBatchCreator) {
    return {
      submitButton: true,
      cancelButton: true,
      addRequestButton: true,
    }
  }

  return {
    submitButton: false,
    cancelButton: false,
    addRequestButton: false,
  }
}

/**
 * Request-level visibility rules (within batch context)
 * Returns which buttons should be visible based on request status, batch status, and user role
 */
export const getRequestActionVisibility = (request, batch, currentUser) => {
  const isCreator = currentUser?.role === 'CREATOR'
  const isApprover = currentUser?.role === 'APPROVER'
  const isBatchCreator = batch?.createdBy === currentUser?.id
  const isClosed = batch?.status === 'COMPLETED' || batch?.status === 'CANCELLED'
  const requestStatus = request?.status

  // CLOSED batch rule: all mutation actions disabled
  if (isClosed) {
    return {
      editButton: false,
      uploadSoaButton: false,
      approveButton: false,
      rejectButton: false,
      markPaidButton: false,
    }
  }

  // PAID state rule: all mutation actions disabled
  if (requestStatus === 'PAID') {
    return {
      editButton: false,
      uploadSoaButton: false,
      approveButton: false,
      rejectButton: false,
      markPaidButton: false,
    }
  }

  // REJECTED state rule: all mutation actions disabled
  if (requestStatus === 'REJECTED') {
    return {
      editButton: false,
      uploadSoaButton: false,
      approveButton: false,
      rejectButton: false,
      markPaidButton: false,
    }
  }

  // DRAFT state
  if (requestStatus === 'DRAFT' && isCreator && isBatchCreator) {
    return {
      editButton: true,
      uploadSoaButton: true,
      approveButton: false,
      rejectButton: false,
      markPaidButton: false,
    }
  }

  // PENDING_APPROVAL state
  if (requestStatus === 'PENDING_APPROVAL' && isApprover) {
    return {
      editButton: false,
      uploadSoaButton: false,
      approveButton: true,
      rejectButton: true,
      markPaidButton: false,
    }
  }

  // APPROVED state
  if (requestStatus === 'APPROVED' && (isCreator || isApprover)) {
    return {
      editButton: false,
      uploadSoaButton: false,
      approveButton: false,
      rejectButton: false,
      markPaidButton: true,
    }
  }

  // SUBMITTED state: no actions
  if (requestStatus === 'SUBMITTED') {
    return {
      editButton: false,
      uploadSoaButton: false,
      approveButton: false,
      rejectButton: false,
      markPaidButton: false,
    }
  }

  return {
    editButton: false,
    uploadSoaButton: false,
    approveButton: false,
    rejectButton: false,
    markPaidButton: false,
  }
}

/**
 * Request-level visibility rules (approval queue context R8)
 */
export const getRequestApprovalQueueVisibility = (request, currentUser) => {
  const isApprover = currentUser?.role === 'APPROVER'
  const requestStatus = request?.status

  if (!isApprover) {
    return {
      approveButton: false,
      rejectButton: false,
      markPaidButton: false,
    }
  }

  // PENDING_APPROVAL state
  if (requestStatus === 'PENDING_APPROVAL') {
    return {
      approveButton: true,
      rejectButton: true,
      markPaidButton: false,
    }
  }

  // APPROVED state
  if (requestStatus === 'APPROVED') {
    return {
      approveButton: false,
      rejectButton: false,
      markPaidButton: true,
    }
  }

  // REJECTED or PAID: no actions
  return {
    approveButton: false,
    rejectButton: false,
    markPaidButton: false,
  }
}
