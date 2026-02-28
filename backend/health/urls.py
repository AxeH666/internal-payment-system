from django.urls import path
from .views import LiveView, ReadyView

urlpatterns = [
    path("live/", LiveView.as_view()),
    path("ready/", ReadyView.as_view()),
]
