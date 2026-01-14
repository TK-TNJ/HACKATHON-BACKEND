"""
SOS Views - API endpoints for emergency SOS requests.

Core endpoints for creating, tracking, and managing SOS requests.
Includes EmergencyCard listing for quick-tap selection.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import SOSRequest
from accounts.models import UserProfile
from .serializers import (
    SOSRequestSerializer,
    SOSCreateSerializer,
    SOSStatusUpdateSerializer,
    SOSListSerializer,
    EmergencyCardSerializer,
)


class EmergencyCardViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing emergency cards (read-only).
    
    Endpoints:
    - GET /sos/cards/ - List all active emergency cards
    - GET /sos/cards/{id}/ - Get specific card details
    
    Cards are pre-defined by admin and displayed on app home screen
    for quick one-tap emergency selection.
    """
    
    queryset = EmergencyCard.objects.filter(is_active=True)
    serializer_class = EmergencyCardSerializer
    
    def list(self, request, *args, **kwargs):
        """
        Return list of active emergency cards for display.
        Ordered by display_order for consistent UI presentation.
        """
        cards = self.get_queryset()
        serializer = self.get_serializer(cards, many=True)
        
        return Response({
            "count": len(serializer.data),
            "cards": serializer.data
        })


class SOSRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for SOSRequest CRUD operations.
    
    Endpoints:
    - GET /sos/ - List all SOS requests
    - POST /sos/ - Create new SOS request (with card selection)
    - GET /sos/{id}/ - Get SOS details
    - PATCH /sos/{id}/ - Update SOS (general)
    - PATCH /sos/{id}/status/ - Update status only
    - POST /sos/{id}/resolve/ - Mark as resolved
    - GET /sos/active/ - List active (unresolved) SOS
    - GET /sos/by-user/{user_id}/ - Get SOS by user
    - GET /sos/bystander-reports/ - List bystander reports only
    """
    
    queryset = SOSRequest.objects.select_related('user', 'selected_card').all()
    
    def get_serializer_class(self):
        """Use different serializers based on action."""
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
        
        Supports:
        - Quick card selection (selected_card field)
        - Additional details text
        - Bystander reporting (is_bystander_report field)
        
        The intelligence app will analyze this after creation.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Infer user from request or body (for custom auth without token)
        try:
            supabase_id = None
            if hasattr(request.user, 'username') and request.user.username:
                 supabase_id = request.user.username
            elif request.user and str(request.user) != 'AnonymousUser':
                 supabase_id = str(request.user)
            
            # Fallback: Check request data for custom auth clients
            if not supabase_id or supabase_id == 'AnonymousUser':
                 supabase_id = request.data.get('supabase_user_id')

            if not supabase_id:
                  return Response(
                     {"error": "User identification required (supabase_user_id)"},
                     status=status.HTTP_400_BAD_REQUEST
                 )

            user_profile = UserProfile.objects.get(supabase_user_id=supabase_id)
            sos = serializer.save(user=user_profile)
        except UserProfile.DoesNotExist:
             # Fallback or error if profile doesn't exist (should verify profile creation on signup)
             # For debug:
             print(f"SOS Create Error: UserProfile not found for {request.user}")
             return Response(
                 {"error": f"UserProfile not found for current user. Please ensure you are registered."},
                 status=status.HTTP_400_BAD_REQUEST
             )
        
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
        Used by internal systems and responders.
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
        Used by responders and coordinators.
        """
        active_statuses = ['created', 'analyzing', 'assigned', 'in_progress']
        active_sos = SOSRequest.objects.filter(
            status__in=active_statuses
        ).select_related('user', 'selected_card')
        serializer = SOSListSerializer(active_sos, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='bystander-reports')
    def list_bystander_reports(self, request):
        """
        Get all bystander reports (someone reporting for another person).
        These are typically higher priority.
        """
        bystander_sos = SOSRequest.objects.filter(
            is_bystander_report=True
        ).select_related('user', 'selected_card')
        serializer = SOSListSerializer(bystander_sos, many=True)
        return Response({
            "count": len(serializer.data),
            "note": "Bystander reports typically have higher urgency",
            "results": serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='by-user/(?P<user_id>[^/.]+)')
    def by_user(self, request, user_id=None):
        """
        Get all SOS requests for a specific user.
        Used for user history and postcare tracking.
        """
        user_sos = SOSRequest.objects.filter(
            user_id=user_id
        ).select_related('selected_card')
        serializer = SOSListSerializer(user_sos, many=True)
        return Response(serializer.data)

