"""
SOS Serializers - API data transformation for emergency requests.
"""

from rest_framework import serializers
from .models import SOSRequest, EmergencyCard


class EmergencyCardSerializer(serializers.ModelSerializer):
    """
    Serializer for EmergencyCard model.
    Used by frontend to display quick-tap emergency cards.
    """
    
    class Meta:
        model = EmergencyCard
        fields = [
            'id',
            'code',
            'name',
            'icon',
            'category',
            'urgency_boost',
            'keywords',
            'display_order',
        ]
        read_only_fields = ['id']


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
    
    # Include card details if selected
    selected_card_details = EmergencyCardSerializer(
        source='selected_card',
        read_only=True
    )
    
    class Meta:
        model = SOSRequest
        fields = [
            'id',
            'user',
            'user_supabase_id',
            # Card selection
            'selected_card',
            'selected_card_details',
            'additional_details',
            # Bystander reporting
            'is_bystander_report',
            'victim_condition',
            'estimated_victims',
            # Location
            'latitude',
            'longitude',
            'location_description',
            # Legacy fields
            'silent_mode',
            'description',
            # Status
            'status',
            'created_at',
            'updated_at',
            'resolved_at',
        ]
        read_only_fields = [
            'id', 'user_supabase_id', 'selected_card_details',
            'created_at', 'updated_at', 'resolved_at'
        ]


class SOSCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new SOS requests.
    
    Supports:
    - Quick card selection (selected_card)
    - Additional details text
    - Bystander reporting fields
    
    Minimal required fields: user, latitude, longitude
    At least one of: selected_card, description, additional_details
    """
    
    class Meta:
        model = SOSRequest
        fields = [
            'id',
            'user',
            # Card selection
            'selected_card',
            'additional_details',
            # Bystander reporting
            'is_bystander_report',
            'victim_condition',
            'estimated_victims',
            # Location
            'latitude',
            'longitude',
            'location_description',
            # Legacy fields
            'silent_mode',
            'description',
            # Read-only
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
    
    # Include card name for quick reference
    card_name = serializers.CharField(
        source='selected_card.name',
        read_only=True,
        default=None
    )
    card_icon = serializers.CharField(
        source='selected_card.icon',
        read_only=True,
        default=None
    )
    
    class Meta:
        model = SOSRequest
        fields = [
            'id',
            'user',
            'card_name',
            'card_icon',
            'is_bystander_report',
            'latitude',
            'longitude',
            'silent_mode',
            'status',
            'created_at',
        ]

