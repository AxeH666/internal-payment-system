"""
URL routing for user endpoints.
"""

from django.urls import path
from apps.users import views

app_name = "users"

urlpatterns = [
    path("me", views.get_current_user, name="current-user"),
    path("", views.list_or_create_users, name="list-or-create-users"),
]
