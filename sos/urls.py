"""
SOS URL Configuration

Routes for emergency SOS request management.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import SOSRequestViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'', SOSRequestViewSet, basename='sos')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]
