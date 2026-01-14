"""
SOS Views - API endpoints for emergency SOS requests.

Core endpoints for creating, tracking, and managing SOS requests.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import SOSRequest
from .serializers import (
    SOSRequestSerializer,
    SOSCreateSerializer,
    SOSStatusUpdateSerializer,
    SOSListSerializer,
)


class SOSRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for SOSRequest CRUD operations.
    
    Endpoints:
    - GET /sos/ - List all SOS requests
    - POST /sos/ - Create new SOS request
    - GET /sos/{id}/ - Get SOS details
    - PATCH /sos/{id}/ - Update SOS (general)
    - PATCH /sos/{id}/status/ - Update status only
    - POST /sos/{id}/resolve/ - Mark as resolved
    - GET /sos/active/ - List active (unresolved) SOS
    - GET /sos/by-user/{user_id}/ - Get SOS by user
    """
    
    queryset = SOSRequest.objects.select_related('user').all()
    
    def get_serializer_class(self):
        """
        Use different serializers based on action.
        """
        if self.action == 'create':
            return SOSCreateSerializer
        elif self.action == 'list':
            return SOSListSerializer
        elif self.action == 'update_status':
            return SOSStatusUpdateSerializer
        return SOSRequestSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Create a new SOS request.
        
        This is the primary entry point for emergencies.
        The intelligence app will analyze this after creation.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sos = serializer.save()
        
        # Return full serializer for response
        response_serializer = SOSRequestSerializer(sos)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        """
        Update only the status of an SOS request.
        
        Used by internal systems and responders to update
        the lifecycle state of an SOS.
        """
        sos = self.get_object()
        serializer = SOSStatusUpdateSerializer(sos, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Status updated",
                "id": sos.id,
                "status": serializer.data['status']
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='resolve')
    def resolve(self, request, pk=None):
        """
        Mark an SOS as resolved.
        
        Sets status to 'resolved' and records resolution timestamp.
        """
        sos = self.get_object()
        sos.mark_resolved()
        
        return Response({
            "message": "SOS marked as resolved",
            "id": sos.id,
            "resolved_at": sos.resolved_at
        })
    
    @action(detail=False, methods=['get'], url_path='active')
    def list_active(self, request):
        """
        Get all active (unresolved) SOS requests.
        
        Used by responders and coordinators to see current emergencies.
        """
        active_statuses = ['created', 'analyzing', 'assigned', 'in_progress']
        active_sos = SOSRequest.objects.filter(status__in=active_statuses)
        serializer = SOSListSerializer(active_sos, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='by-user/(?P<user_id>[^/.]+)')
    def by_user(self, request, user_id=None):
        """
        Get all SOS requests for a specific user.
        
        Used for user history and postcare tracking.
        """
        user_sos = SOSRequest.objects.filter(user_id=user_id)
        serializer = SOSListSerializer(user_sos, many=True)
        return Response(serializer.data)
