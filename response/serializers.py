"""
Response Serializers - API data transformation for assignments.
"""

from rest_framework import serializers
from .models import ResponderAssignment, AuthorityEscalation


class ResponderAssignmentSerializer(serializers.ModelSerializer):
    """
    Full serializer for ResponderAssignment model.
    """
    
    # Include related info
    sos_id = serializers.IntegerField(source='sos.id', read_only=True)
    responder_id = serializers.IntegerField(source='responder.id', read_only=True)
    responder_supabase_id = serializers.CharField(
        source='responder.user.supabase_user_id',
        read_only=True
    )
    
    class Meta:
        model = ResponderAssignment
        fields = [
            'id',
            'sos',
            'sos_id',
            'responder',
            'responder_id',
            'responder_supabase_id',
            'status',
            'assigned_at',
            'accepted_at',
            'completed_at',
            'responder_notes',
        ]
        read_only_fields = ['id', 'assigned_at', 'accepted_at', 'completed_at']


class AssignmentCreateSerializer(serializers.Serializer):
    """
    Serializer for creating new assignments.
    """
    
    sos_id = serializers.IntegerField()
    responder_id = serializers.IntegerField()


class AssignmentStatusSerializer(serializers.ModelSerializer):
    """
    Serializer for updating assignment status only.
    """
    
    class Meta:
        model = ResponderAssignment
        fields = ['status', 'responder_notes']


class MatchingRequestSerializer(serializers.Serializer):
    """
    Input serializer for matching requests.
    """
    
    required_skills = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    max_distance_km = serializers.FloatField(required=False, default=50.0)
    limit = serializers.IntegerField(required=False, default=10)


class MatchedResponderSerializer(serializers.Serializer):
    """
    Output serializer for matched responders.
    """
    
    responder_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    supabase_user_id = serializers.CharField()
    skills = serializers.ListField(child=serializers.CharField())
    reputation_score = serializers.IntegerField()
    match_score = serializers.FloatField()
    match_reasons = serializers.ListField(child=serializers.CharField())
    matched_skills = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    distance_km = serializers.FloatField(
        required=False,
        allow_null=True
    )


class AuthorityEscalationSerializer(serializers.ModelSerializer):
    """
    Serializer for AuthorityEscalation model.
    """
    
    class Meta:
        model = AuthorityEscalation
        fields = [
            'id',
            'sos',
            'authority_type',
            'reason',
            'escalated_at',
            'authority_reference',
        ]
        read_only_fields = ['id', 'escalated_at', 'authority_reference']


class EscalationCreateSerializer(serializers.Serializer):
    """
    Input serializer for creating escalations.
    """
    
    sos_id = serializers.IntegerField()
    authority_type = serializers.ChoiceField(
        choices=['police', 'fire', 'medical', 'other']
    )
    reason = serializers.CharField()
