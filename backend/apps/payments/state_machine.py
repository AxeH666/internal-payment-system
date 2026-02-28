"""
State machine enforcement for PaymentRequest and PaymentBatch.

Validates state transitions according to 03_STATE_MACHINE.md.
Raises InvalidStateError for disallowed transitions.
"""

from core.exceptions import InvalidStateError

# Allowed transitions for PaymentRequest
PAYMENT_REQUEST_TRANSITIONS = {
    "DRAFT": ["SUBMITTED", "DRAFT"],  # DRAFT -> DRAFT is edit (no state change)
    "SUBMITTED": ["PENDING_APPROVAL"],
    "PENDING_APPROVAL": ["APPROVED", "REJECTED"],
    "APPROVED": ["PAID"],
    "REJECTED": [],  # Terminal
    "PAID": [],  # Terminal
}

# Allowed transitions for PaymentBatch
PAYMENT_BATCH_TRANSITIONS = {
    "DRAFT": ["SUBMITTED", "CANCELLED"],
    "SUBMITTED": ["PROCESSING"],
    "PROCESSING": ["COMPLETED"],
    "COMPLETED": [],  # Terminal
    "CANCELLED": [],  # Terminal
}


def validate_transition(entity_type, current_status, target_status):
    """
    Validate a state transition.

    Args:
        entity_type: 'PaymentRequest' or 'PaymentBatch'
        current_status: Current state
        target_status: Target state

    Returns:
        bool: True if transition is allowed

    Raises:
        InvalidStateError: If transition is disallowed
    """
    if entity_type == "PaymentRequest":
        transitions = PAYMENT_REQUEST_TRANSITIONS
    elif entity_type == "PaymentBatch":
        transitions = PAYMENT_BATCH_TRANSITIONS
    else:
        raise ValueError(f"Unknown entity_type: {entity_type}")

    if current_status not in transitions:
        raise InvalidStateError(
            f"Invalid current status: {current_status}",
            {"entity_type": entity_type, "current_status": current_status},
        )

    allowed_targets = transitions[current_status]

    # Check if target is terminal (no transitions allowed)
    if not allowed_targets:
        raise InvalidStateError(
            (
                f"{entity_type} in state {current_status} is terminal and cannot "
                "transition"
            ),
            {
                "entity_type": entity_type,
                "current_status": current_status,
                "target_status": target_status,
            },
        )

    # Allow same-state transitions for DRAFT (edits)
    if current_status == target_status and current_status == "DRAFT":
        return True

    if target_status not in allowed_targets:
        raise InvalidStateError(
            (
                "Invalid transition: "
                f"{entity_type} cannot transition from {current_status} to "
                f"{target_status}"
            ),
            {
                "entity_type": entity_type,
                "current_status": current_status,
                "target_status": target_status,
                "allowed_transitions": allowed_targets,
            },
        )

    return True


def is_terminal_state(entity_type, status):
    """Check if a state is terminal (no transitions allowed)."""
    if entity_type == "PaymentRequest":
        transitions = PAYMENT_REQUEST_TRANSITIONS
    elif entity_type == "PaymentBatch":
        transitions = PAYMENT_BATCH_TRANSITIONS
    else:
        return False

    return status in transitions and len(transitions[status]) == 0


def is_closed_batch(status):
    """Check if batch status is COMPLETED or CANCELLED (closed)."""
    return status in ("COMPLETED", "CANCELLED")
