"""
Version locking helper for PaymentRequest state transitions.
Prevents concurrent modification corruption.
"""
from django.db.models import F
from core.exceptions import InvalidStateError


def version_locked_update(queryset, current_version, **updates):
    """
    Perform version-locked update on queryset.

    Args:
        queryset: Django QuerySet to update
        current_version: Expected current version number
        **updates: Fields to update

    Returns:
        int: Number of rows updated (should be 1)

    Raises:
        InvalidStateError: If version mismatch (concurrent modification detected)
    """
    updated_count = queryset.filter(version=current_version).update(
        **updates,
        version=F("version") + 1,
    )

    if updated_count == 0:
        raise InvalidStateError(
            "Concurrent modification detected. Version mismatch or invalid state.",
            {"expected_version": current_version},
        )

    return updated_count
