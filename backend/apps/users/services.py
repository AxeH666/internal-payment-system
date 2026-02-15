"""
Service-layer functions for the Users app.

This module exists to keep models passive:
- No business logic in models
- No permission logic in models
- Persistence orchestration (create/save) lives here
"""

from __future__ import annotations

from typing import Any, Optional, Type


def create_user(
    *,
    user_model: Type[Any],
    username: str,
    password: Optional[str] = None,
    display_name: Optional[str] = None,
    role: str = "VIEWER",
    using: Optional[str] = None,
    **extra_fields: Any,
):
    """
    Create and persist a user.

    Behavior is intentionally identical to the previous UserManager.create_user.
    """
    if not username:
        raise ValueError("The username field must be set")

    user = user_model(
        username=username,
        display_name=display_name or username,
        role=role,
        **extra_fields,
    )
    user.set_password(password)
    if using is None:
        user.save()
    else:
        user.save(using=using)
    return user


def create_superuser(
    *,
    user_model: Type[Any],
    username: str,
    password: Optional[str] = None,
    using: Optional[str] = None,
    **extra_fields: Any,
):
    """
    Create a "superuser" per existing project semantics.

    Note: In this codebase, role 'CREATOR' is treated as staff/superuser
    for Django admin compatibility (no schema changes introduced here).
    """
    extra_fields.setdefault("role", "CREATOR")
    return create_user(
        user_model=user_model,
        username=username,
        password=password,
        using=using,
        **extra_fields,
    )


def user_is_staff(*, user: Any) -> bool:
    """Django admin compatibility predicate."""
    return user.role == "CREATOR"


def user_is_superuser(*, user: Any) -> bool:
    """Django admin compatibility predicate."""
    return user.role == "CREATOR"


def user_has_perm(*, user: Any, perm: str, obj: Any = None) -> bool:
    """Django admin compatibility predicate."""
    _ = (perm, obj)
    return user.role == "CREATOR"


def user_has_module_perms(*, user: Any, app_label: str) -> bool:
    """Django admin compatibility predicate."""
    _ = app_label
    return user.role == "CREATOR"
