"""
Accounts URL Configuration

Routes for user and responder profile management.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserProfileViewSet, ResponderProfileViewSet, LoginView

# Create router and register viewsets
router = DefaultRouter()
router.register(r'users', UserProfileViewSet, basename='user')
router.register(r'responders', ResponderProfileViewSet, basename='responder')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
    path('login/', LoginView.as_view(), name='login'),
]
