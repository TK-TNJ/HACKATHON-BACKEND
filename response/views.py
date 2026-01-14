"""
Response Views - API endpoints for matching and coordination.

Handles responder matching, assignment, and authority escalation.
"""

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ResponderAssignment, AuthorityEscalation
from .serializers import (
    ResponderAssignmentSerializer,
    AssignmentCreateSerializer,
    AssignmentStatusSerializer,
    MatchingRequestSerializer,
    MatchedResponderSerializer,
    AuthorityEscalationSerializer,
    EscalationCreateSerializer,
)
from .services import find_matching_responders, assign_responder, escalate_to_authority
from sos.models import SOSRequest
from accounts.models import ResponderProfile


class MatchingView(APIView):
    """
    Find matching responders for an SOS request.
    
    GET /response/match/{sos_id}/
    POST /response/match/{sos_id}/ (with optional filters)
    
    Returns a ranked list of suitable responders.
    """
    
    def get(self, request, sos_id):
        """Get matching responders with default parameters."""
        try:
            sos = SOSRequest.objects.get(id=sos_id)
        except SOSRequest.DoesNotExist:
            return Response(
                {"error": f"SOS request {sos_id} not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        matches = find_matching_responders(sos)
        serializer = MatchedResponderSerializer(matches, many=True)
        
        return Response({
            "sos_id": sos_id,
            "matches_found": len(matches),
            "responders": serializer.data
        })
    
    def post(self, request, sos_id):
        """Get matching responders with custom filters."""
        try:
            sos = SOSRequest.objects.get(id=sos_id)
        except SOSRequest.DoesNotExist:
            return Response(
                {"error": f"SOS request {sos_id} not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate input
        input_serializer = MatchingRequestSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(
                input_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = input_serializer.validated_data
        matches = find_matching_responders(
            sos,
            required_skills=data.get('required_skills'),
            max_distance_km=data.get('max_distance_km', 50.0),
            limit=data.get('limit', 10)
        )
        
        serializer = MatchedResponderSerializer(matches, many=True)
        
        return Response({
            "sos_id": sos_id,
            "matches_found": len(matches),
            "filters_applied": data,
            "responders": serializer.data
        })


class AssignView(APIView):
    """
    Assign a responder to an SOS request.
    
    POST /response/assign/
    """
    
    def post(self, request):
        """Create a new assignment."""
        
        serializer = AssignmentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        
        # Get SOS and Responder
        try:
            sos = SOSRequest.objects.get(id=data['sos_id'])
        except SOSRequest.DoesNotExist:
            return Response(
                {"error": f"SOS request {data['sos_id']} not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            responder = ResponderProfile.objects.get(id=data['responder_id'])
        except ResponderProfile.DoesNotExist:
            return Response(
                {"error": f"Responder {data['responder_id']} not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if responder is available
        if not responder.is_available:
            return Response(
                {"error": "Responder is not currently available"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create assignment
        assignment = assign_responder(sos, responder)
        
        # Return created assignment
        output_serializer = ResponderAssignmentSerializer(assignment)
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED
        )


class ResponderAssignmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing responder assignments.
    
    Endpoints:
    - GET /response/assignments/ - List assignments
    - GET /response/assignments/{id}/ - Get assignment details
    - PATCH /response/assignments/{id}/ - Update assignment
    - PATCH /response/assignments/{id}/accept/ - Accept assignment
    - PATCH /response/assignments/{id}/complete/ - Complete assignment
    - GET /response/assignments/by-sos/{sos_id}/ - Get assignments for SOS
    - GET /response/assignments/by-responder/{responder_id}/ - Get responder's assignments
    """
    
    queryset = ResponderAssignment.objects.select_related(
        'sos', 'responder', 'responder__user'
    ).all()
    serializer_class = ResponderAssignmentSerializer
    
    @action(detail=True, methods=['patch'], url_path='accept')
    def accept(self, request, pk=None):
        """Accept an assignment (responder action)."""
        assignment = self.get_object()
        assignment.accept()
        
        return Response({
            "message": "Assignment accepted",
            "id": assignment.id,
            "status": assignment.status,
            "accepted_at": assignment.accepted_at
        })
    
    @action(detail=True, methods=['patch'], url_path='complete')
    def complete(self, request, pk=None):
        """Complete an assignment."""
        assignment = self.get_object()
        notes = request.data.get('responder_notes')
        assignment.complete(notes=notes)
        
        return Response({
            "message": "Assignment completed",
            "id": assignment.id,
            "status": assignment.status,
            "completed_at": assignment.completed_at
        })
    
    @action(detail=False, methods=['get'], url_path='by-sos/(?P<sos_id>[^/.]+)')
    def by_sos(self, request, sos_id=None):
        """Get all assignments for a specific SOS."""
        assignments = ResponderAssignment.objects.filter(sos_id=sos_id)
        serializer = self.get_serializer(assignments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='by-responder/(?P<responder_id>[^/.]+)')
    def by_responder(self, request, responder_id=None):
        """Get all assignments for a specific responder."""
        assignments = ResponderAssignment.objects.filter(responder_id=responder_id)
        serializer = self.get_serializer(assignments, many=True)
        return Response(serializer.data)


class EscalationView(APIView):
    """
    Escalate SOS to authorities.
    
    POST /response/escalate/
    
    This is a mock endpoint for MVP. In production, this would
    integrate with actual emergency services.
    """
    
    def post(self, request):
        """Create a new authority escalation."""
        
        serializer = EscalationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        
        # Get SOS
        try:
            sos = SOSRequest.objects.get(id=data['sos_id'])
        except SOSRequest.DoesNotExist:
            return Response(
                {"error": f"SOS request {data['sos_id']} not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create escalation
        escalation = escalate_to_authority(
            sos=sos,
            authority_type=data['authority_type'],
            reason=data['reason']
        )
        
        output_serializer = AuthorityEscalationSerializer(escalation)
        
        return Response({
            "message": f"Escalated to {data['authority_type']}",
            "note": "This is a mock escalation for MVP",
            "escalation": output_serializer.data
        }, status=status.HTTP_201_CREATED)
