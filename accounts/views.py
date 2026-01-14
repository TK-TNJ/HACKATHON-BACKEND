"""
Accounts Views - API endpoints for user and responder profiles.

Note: No login/signup endpoints here - auth is handled by Supabase.
These endpoints manage profile data only.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import UserProfile, ResponderProfile
from .serializers import (
    UserProfileSerializer,
    UserProfileCreateSerializer,
    ResponderProfileSerializer,
    ResponderAvailabilitySerializer,
    ResponderLocationSerializer,
)


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for UserProfile CRUD operations.
    
    Endpoints:
    - GET /users/ - List all users
    - POST /users/ - Create new user profile
    - GET /users/{id}/ - Get user profile
    - PATCH /users/{id}/ - Update user profile
    - DELETE /users/{id}/ - Delete user profile
    - GET /users/by-supabase/{supabase_id}/ - Get by Supabase ID
    """
    
    queryset = UserProfile.objects.all()
    
    def get_serializer_class(self):
        """Use different serializer for create action."""
        if self.action == 'create':
            return UserProfileCreateSerializer
        return UserProfileSerializer
    
    @action(detail=False, methods=['get'], url_path='by-supabase/(?P<supabase_id>[^/.]+)')
    def by_supabase_id(self, request, supabase_id=None):
        """
        Get user profile by Supabase user ID.
        
        This is the primary way to look up users from the frontend,
        since the frontend only has access to the Supabase user ID.
        """
        try:
            user = UserProfile.objects.get(supabase_user_id=supabase_id)
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "User profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class ResponderProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ResponderProfile CRUD operations.
    
    Endpoints:
    - GET /responders/ - List all responders
    - POST /responders/ - Create responder profile
    - GET /responders/{id}/ - Get responder profile
    - PATCH /responders/{id}/ - Update responder profile
    - PATCH /responders/{id}/availability/ - Update availability only
    - PATCH /responders/{id}/location/ - Update location only
    - GET /responders/available/ - List available responders
    - GET /responders/by-skill/{skill}/ - Filter by skill
    """
    
    queryset = ResponderProfile.objects.select_related('user').all()
    serializer_class = ResponderProfileSerializer
    
    @action(detail=True, methods=['patch'], url_path='availability')
    def update_availability(self, request, pk=None):
        """
        Quick endpoint to toggle responder availability.
        Used when responder goes on/off duty.
        """
        responder = self.get_object()
        serializer = ResponderAvailabilitySerializer(
            responder, 
            data=request.data, 
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Availability updated",
                "is_available": serializer.data['is_available']
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'], url_path='location')
    def update_location(self, request, pk=None):
        """
        Update responder's last known location.
        Used for proximity-based matching.
        """
        responder = self.get_object()
        serializer = ResponderLocationSerializer(
            responder,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Location updated",
                "latitude": serializer.data['last_known_latitude'],
                "longitude": serializer.data['last_known_longitude']
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='available')
    def list_available(self, request):
        """
        Get list of all currently available responders.
        Used by the matching algorithm.
        """
        available = ResponderProfile.objects.filter(is_available=True)
        serializer = self.get_serializer(available, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='by-skill/(?P<skill>[^/.]+)')
    def by_skill(self, request, skill=None):
        """
        Filter responders by a specific skill.
        
        Skills are stored as JSON array, so we use contains lookup.
        Example: /responders/by-skill/first_aid/
        """
        # Filter responders whose skills contain the requested skill
        responders = ResponderProfile.objects.filter(
            skills__contains=[skill],
            is_available=True
        )
        serializer = self.get_serializer(responders, many=True)
        return Response(serializer.data)
