"""
SOS URL Configuration

Routes for emergency SOS request management and emergency cards.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import SOSRequestViewSet, EmergencyCardViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'cards', EmergencyCardViewSet, basename='emergency-card')
router.register(r'', SOSRequestViewSet, basename='sos')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]

