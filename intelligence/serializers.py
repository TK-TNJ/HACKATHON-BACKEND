"""
Intelligence Serializers - API data transformation for analysis endpoints.
"""

from rest_framework import serializers


class SOSAnalysisInputSerializer(serializers.Serializer):
    """
    Input serializer for SOS analysis.
    Accepts SOS data for analysis.
    """
    
    sos_id = serializers.IntegerField(required=False, help_text="ID of existing SOS request")
    latitude = serializers.DecimalField(
        max_digits=9, 
        decimal_places=6,
        required=False
    )
    longitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False
    )
    silent_mode = serializers.BooleanField(default=False)
    description = serializers.CharField(
        required=False, 
        allow_blank=True,
        help_text="Emergency description or keywords"
    )
    created_at = serializers.DateTimeField(required=False)
    use_llm = serializers.BooleanField(
        default=True,
        help_text="Whether to use LLM for enhanced analysis"
    )


class SOSAnalysisOutputSerializer(serializers.Serializer):
    """
    Output serializer for SOS analysis results.
    Includes both rule-based and LLM fields.
    """
    
    # Urgency data
    urgency_score = serializers.IntegerField()
    severity_level = serializers.CharField()
    urgency_factors = serializers.ListField(child=serializers.CharField())
    
    # Classification data
    emergency_type = serializers.CharField()
    classification_confidence = serializers.FloatField()
    matched_keywords = serializers.ListField(child=serializers.CharField())
    classification_reasoning = serializers.CharField()
    
    # Recommendations
    recommended_skills = serializers.ListField(child=serializers.CharField())
    needs_authority_escalation = serializers.BooleanField()
    
    # LLM-enhanced fields (optional)
    panic_level = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=10,
        help_text="Emotional distress level (1-10), from LLM"
    )
    emotional_state = serializers.CharField(
        required=False,
        help_text="Detected emotional state (calm/anxious/panicked/distressed/fearful)"
    )
    llm_reasoning = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="LLM explanation of analysis"
    )
    analysis_method = serializers.CharField(
        default='rule_based',
        help_text="Method used: 'rule_based', 'llm', or 'hybrid'"
    )
    
    # Metadata
    analysis_timestamp = serializers.CharField()
