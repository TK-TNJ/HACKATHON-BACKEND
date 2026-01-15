"""
Accounts Serializers - API data transformation for user profiles.
"""

from rest_framework import serializers
from .models import UserProfile, ResponderProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for UserProfile model.
    
    Read-only fields: supabase_user_id, created_at (set by system)
    Writable fields: role, trust_score
    """
    
    class Meta:
        model = UserProfile
        fields = [
            'id',
            'supabase_user_id',
            'role',
            'trust_score',
            'emergency_contacts',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'supabase_user_id', 'created_at', 'updated_at']


class UserProfileCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new UserProfile.
    Allows setting supabase_user_id during creation.
    """
    
    class Meta:
        model = UserProfile
        fields = [
            'id',
            'supabase_user_id',
            'role',
            'trust_score',
            'created_at',
            'email',
            'password',
        ]
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = super().create(validated_data)
        if password:
            from django.contrib.auth.hashers import make_password
            instance.password = make_password(password)
            instance.save()
        return instance


class ResponderProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for ResponderProfile model.
    
    Includes nested user data for convenience.
    """
    
    # Include basic user info in response
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    supabase_user_id = serializers.CharField(
        source='user.supabase_user_id', 
        read_only=True
    )
    
    class Meta:
        model = ResponderProfile
        fields = [
            'id',
            'user_id',
            'supabase_user_id',
            'skills',
            'is_available',
            'reputation_score',
            'last_known_latitude',
            'last_known_longitude',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user_id', 'supabase_user_id', 'created_at', 'updated_at']


class ResponderAvailabilitySerializer(serializers.ModelSerializer):
    """
    Minimal serializer for updating responder availability only.
    """
    
    class Meta:
        model = ResponderProfile
        fields = ['is_available']


class ResponderLocationSerializer(serializers.ModelSerializer):
    """
    Serializer for updating responder's last known location.
    """
    
    class Meta:
        model = ResponderProfile
        fields = ['last_known_latitude', 'last_known_longitude']
