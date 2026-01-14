"""
Postcare URL Configuration

Routes for feedback, follow-up, and metrics endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    IncidentFeedbackViewSet,
    FollowUpViewSet,
    ImpactMetricsView,
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'feedback', IncidentFeedbackViewSet, basename='feedback')
router.register(r'followup', FollowUpViewSet, basename='followup')

urlpatterns = [
    # Metrics endpoint
    path('metrics/', ImpactMetricsView.as_view(), name='metrics'),
    
    # ViewSet routes
    path('', include(router.urls)),
]
