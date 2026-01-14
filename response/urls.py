"""
Response URL Configuration

Routes for matching, assignment, and escalation endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    MatchingView,
    AssignView,
    ResponderAssignmentViewSet,
    EscalationView,
)

# Create router for ViewSet
router = DefaultRouter()
router.register(r'assignments', ResponderAssignmentViewSet, basename='assignment')

urlpatterns = [
    # Matching endpoint
    path('match/<int:sos_id>/', MatchingView.as_view(), name='matching'),
    
    # Assign endpoint
    path('assign/', AssignView.as_view(), name='assign'),
    
    # Escalate endpoint
    path('escalate/', EscalationView.as_view(), name='escalate'),
    
    # ViewSet routes
    path('', include(router.urls)),
]
