"""
Intelligence URL Configuration

Routes for emergency analysis endpoints.
"""

from django.urls import path

from .views import (
    AnalyzeSOSView,
    AnalyzeSOSRuleBasedView,
    UrgencyOnlyView,
    ClassifyOnlyView
)

urlpatterns = [
    # Main hybrid analysis endpoint (LLM + fallback)
    path('analyze/', AnalyzeSOSView.as_view(), name='analyze-sos'),
    
    # Rule-based only (no LLM, faster)
    path('analyze-rules/', AnalyzeSOSRuleBasedView.as_view(), name='analyze-rules'),
    
    # Lightweight endpoints
    path('urgency/', UrgencyOnlyView.as_view(), name='urgency-only'),
    path('classify/', ClassifyOnlyView.as_view(), name='classify-only'),
]
