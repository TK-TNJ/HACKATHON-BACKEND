"""
Intelligence URL Configuration

Routes for emergency analysis endpoints.
"""

from django.urls import path

from .views import AnalyzeSOSView, UrgencyOnlyView, ClassifyOnlyView

urlpatterns = [
    # Main analysis endpoint
    path('analyze/', AnalyzeSOSView.as_view(), name='analyze-sos'),
    
    # Lightweight endpoints
    path('urgency/', UrgencyOnlyView.as_view(), name='urgency-only'),
    path('classify/', ClassifyOnlyView.as_view(), name='classify-only'),
]
