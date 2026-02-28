"""
User model for the Internal Payment Workflow System.

Fields: id (UUID), username, display_name, role, password, created_at, updated_at.
Username unique. Role choices CREATOR, APPROVER, VIEWER, ADMIN.
"""

import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.core.validators import RegexValidator

from . import services


class Role(models.TextChoices):
    ADMIN = "ADMIN"
    CREATOR = "CREATOR"
    APPROVER = "APPROVER"
    VIEWER = "VIEWER"


class UserManager(BaseUserManager):
    """Custom user manager."""

    def create_user(
        self, username, password=None, display_name=None, role="VIEWER", **extra_fields
    ):
        return services.create_user(
            user_model=self.model,
            username=username,
            password=password,
            display_name=display_name,
            role=role,
            using=self._db,
            **extra_fields,
        )

    def create_superuser(self, username, password=None, **extra_fields):
        return services.create_superuser(
            user_model=self.model,
            username=username,
            password=password,
            using=self._db,
            **extra_fields,
        )


class User(AbstractBaseUser):
    """Custom User model with UUID primary key and role field."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^[\w.@+-]+$",
                message=(
                    "Username may contain only letters, numbers, and @/./+/-/_ "
                    "characters."
                ),
            )
        ],
    )
    display_name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=Role.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["display_name", "role"]

    objects = UserManager()

    class Meta:
        db_table = "users"
        constraints = [
            models.CheckConstraint(
                check=models.Q(role__in=["CREATOR", "APPROVER", "VIEWER", "ADMIN"]),
                name="valid_role",
            )
        ]

    def __str__(self):
        return self.username

    @property
    def is_staff(self):
        """Required for Django admin compatibility."""
        return services.user_is_staff(user=self)

    @property
    def is_superuser(self):
        """Required for Django admin compatibility."""
        return services.user_is_superuser(user=self)

    def has_perm(self, perm, obj=None):
        """Required for Django admin compatibility."""
        return services.user_has_perm(user=self, perm=perm, obj=obj)

    def has_module_perms(self, app_label):
        """Required for Django admin compatibility."""
        return services.user_has_module_perms(user=self, app_label=app_label)
