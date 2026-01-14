"""
Postcare Serializers - API data transformation for feedback and follow-up.
"""

from rest_framework import serializers
from .models import IncidentFeedback, FollowUp


class IncidentFeedbackSerializer(serializers.ModelSerializer):
    """
    Serializer for IncidentFeedback model.
    """
    
    sos_id = serializers.IntegerField(source='sos.id', read_only=True)
    
    class Meta:
        model = IncidentFeedback
        fields = [
            'id',
            'sos',
            'sos_id',
            'rating',
            'comment',
            'was_helpful',
            'would_recommend',
            'submitted_at',
        ]
        read_only_fields = ['id', 'sos_id', 'submitted_at']
    
    def validate_rating(self, value):
        """Ensure rating is between 1 and 5."""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value


class FollowUpSerializer(serializers.ModelSerializer):
    """
    Serializer for FollowUp model.
    """
    
    sos_id = serializers.IntegerField(source='sos.id', read_only=True)
    
    class Meta:
        model = FollowUp
        fields = [
            'id',
            'sos',
            'sos_id',
            'is_safe',
            'notes',
            'needs_support',
            'support_type',
            'followup_time',
        ]
        read_only_fields = ['id', 'sos_id', 'followup_time']


class ImpactMetricsSerializer(serializers.Serializer):
    """
    Serializer for impact metrics output.
    """
    
    # Overall stats
    total_sos_requests = serializers.IntegerField()
    resolved_requests = serializers.IntegerField()
    resolution_rate = serializers.FloatField()
    
    # Response stats
    total_responders = serializers.IntegerField()
    average_response_time_minutes = serializers.FloatField(allow_null=True)
    
    # Feedback stats
    total_feedback = serializers.IntegerField()
    average_rating = serializers.FloatField(allow_null=True)
    recommendation_rate = serializers.FloatField(allow_null=True)
    
    # Follow-up stats
    total_followups = serializers.IntegerField()
    safety_confirmation_rate = serializers.FloatField(allow_null=True)
    
    # Time period
    metrics_period = serializers.CharField()
