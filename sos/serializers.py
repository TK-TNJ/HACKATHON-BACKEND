"""
SOS Serializers - API data transformation for emergency requests.
"""

from rest_framework import serializers
from .models import SOSRequest


class SOSRequestSerializer(serializers.ModelSerializer):
    """
    Full serializer for SOSRequest model.
    Used for read operations and detailed responses.
    """
    
    # Include user info for context
    user_supabase_id = serializers.CharField(
        source='user.supabase_user_id',
        read_only=True
    )
    
    class Meta:
        model = SOSRequest
        fields = [
            'id',
            'user',
            'user_supabase_id',
            'latitude',
            'longitude',
            'location_description',
            'silent_mode',
            'description',
            'status',
            'created_at',
            'updated_at',
            'resolved_at',
        ]
        read_only_fields = ['id', 'user_supabase_id', 'created_at', 'updated_at', 'resolved_at']


class SOSCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new SOS requests.
    
    Minimal required fields: user, latitude, longitude
    Optional: silent_mode, description, location_description
    """
    
    class Meta:
        model = SOSRequest
        fields = [
            'id',
            'user',
            'latitude',
            'longitude',
            'location_description',
            'silent_mode',
            'description',
            'status',
            'created_at',
        ]
        read_only_fields = ['id', 'status', 'created_at', 'user']


class SOSStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating SOS status only.
    Used by internal systems/responders.
    """
    
    class Meta:
        model = SOSRequest
        fields = ['status']


class SOSListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing SOS requests.
    Excludes some fields for performance.
    """
    
    class Meta:
        model = SOSRequest
        fields = [
            'id',
            'user',
            'latitude',
            'longitude',
            'silent_mode',
            'status',
            'created_at',
        ]
