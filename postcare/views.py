"""
Postcare Views - API endpoints for feedback, follow-up, and metrics.

Handles post-incident care and impact tracking.
"""

from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import IncidentFeedback, FollowUp
from .serializers import (
    IncidentFeedbackSerializer,
    FollowUpSerializer,
    ImpactMetricsSerializer,
)
from sos.models import SOSRequest
from accounts.models import ResponderProfile


class IncidentFeedbackViewSet(viewsets.ModelViewSet):
    """
    ViewSet for incident feedback.
    
    Endpoints:
    - GET /postcare/feedback/ - List all feedback
    - POST /postcare/feedback/ - Submit feedback
    - GET /postcare/feedback/{id}/ - Get feedback details
    - GET /postcare/feedback/by-sos/{sos_id}/ - Get feedback for SOS
    """
    
    queryset = IncidentFeedback.objects.select_related('sos').all()
    serializer_class = IncidentFeedbackSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Submit feedback for a resolved SOS.
        
        Validates that the SOS exists and is resolved.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check if SOS is resolved
        sos_id = serializer.validated_data['sos'].id
        try:
            sos = SOSRequest.objects.get(id=sos_id)
            if sos.status != 'resolved':
                return Response(
                    {"error": "Feedback can only be submitted for resolved SOS requests"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except SOSRequest.DoesNotExist:
            return Response(
                {"error": f"SOS request {sos_id} not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if feedback already exists
        if IncidentFeedback.objects.filter(sos_id=sos_id).exists():
            return Response(
                {"error": "Feedback already submitted for this SOS"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    @action(detail=False, methods=['get'], url_path='by-sos/(?P<sos_id>[^/.]+)')
    def by_sos(self, request, sos_id=None):
        """Get feedback for a specific SOS."""
        try:
            feedback = IncidentFeedback.objects.get(sos_id=sos_id)
            serializer = self.get_serializer(feedback)
            return Response(serializer.data)
        except IncidentFeedback.DoesNotExist:
            return Response(
                {"error": "No feedback found for this SOS"},
                status=status.HTTP_404_NOT_FOUND
            )


class FollowUpViewSet(viewsets.ModelViewSet):
    """
    ViewSet for follow-up check-ins.
    
    Endpoints:
    - GET /postcare/followup/ - List all follow-ups
    - POST /postcare/followup/ - Submit follow-up
    - GET /postcare/followup/{id}/ - Get follow-up details
    - GET /postcare/followup/by-sos/{sos_id}/ - Get follow-ups for SOS
    - GET /postcare/followup/needs-support/ - List needing support
    """
    
    queryset = FollowUp.objects.select_related('sos').all()
    serializer_class = FollowUpSerializer
    
    @action(detail=False, methods=['get'], url_path='by-sos/(?P<sos_id>[^/.]+)')
    def by_sos(self, request, sos_id=None):
        """Get all follow-ups for a specific SOS."""
        followups = FollowUp.objects.filter(sos_id=sos_id)
        serializer = self.get_serializer(followups, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='needs-support')
    def needs_support(self, request):
        """Get all follow-ups where user needs additional support."""
        needs_support = FollowUp.objects.filter(needs_support=True)
        serializer = self.get_serializer(needs_support, many=True)
        return Response(serializer.data)


class ImpactMetricsView(APIView):
    """
    Get impact metrics for the platform.
    
    GET /postcare/metrics/
    GET /postcare/metrics/?days=30 (custom time period)
    
    Returns aggregate statistics about platform impact.
    """
    
    def get(self, request):
        """Calculate and return impact metrics."""
        
        # Get time period (default: last 30 days)
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        # SOS Statistics
        total_sos = SOSRequest.objects.filter(
            created_at__gte=start_date
        ).count()
        
        resolved_sos = SOSRequest.objects.filter(
            created_at__gte=start_date,
            status='resolved'
        ).count()
        
        resolution_rate = (resolved_sos / total_sos * 100) if total_sos > 0 else 0
        
        # Responder Statistics
        total_responders = ResponderProfile.objects.count()
        
        # For MVP, we don't have actual response time tracking
        # This would be calculated from assignment acceptance times in production
        average_response_time = None
        
        # Feedback Statistics
        feedback_qs = IncidentFeedback.objects.filter(
            submitted_at__gte=start_date
        )
        total_feedback = feedback_qs.count()
        
        avg_rating = feedback_qs.aggregate(avg=Avg('rating'))['avg']
        
        if total_feedback > 0:
            recommend_count = feedback_qs.filter(would_recommend=True).count()
            recommendation_rate = (recommend_count / total_feedback * 100)
        else:
            recommendation_rate = None
        
        # Follow-up Statistics
        followup_qs = FollowUp.objects.filter(
            followup_time__gte=start_date
        )
        total_followups = followup_qs.count()
        
        if total_followups > 0:
            safe_count = followup_qs.filter(is_safe=True).count()
            safety_rate = (safe_count / total_followups * 100)
        else:
            safety_rate = None
        
        # Build response
        metrics = {
            'total_sos_requests': total_sos,
            'resolved_requests': resolved_sos,
            'resolution_rate': round(resolution_rate, 1),
            'total_responders': total_responders,
            'average_response_time_minutes': average_response_time,
            'total_feedback': total_feedback,
            'average_rating': round(avg_rating, 2) if avg_rating else None,
            'recommendation_rate': round(recommendation_rate, 1) if recommendation_rate else None,
            'total_followups': total_followups,
            'safety_confirmation_rate': round(safety_rate, 1) if safety_rate else None,
            'metrics_period': f'Last {days} days',
        }
        
        serializer = ImpactMetricsSerializer(metrics)
        return Response(serializer.data)
