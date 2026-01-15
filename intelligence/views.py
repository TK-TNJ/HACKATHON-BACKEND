"""
Intelligence Views - API endpoints for emergency analysis.

These endpoints provide the "brain" functionality for analyzing
SOS requests and determining urgency/classification.

Supports both rule-based and LLM-enhanced (hybrid) analysis.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .services import analyze_sos, analyze_sos_hybrid, calculate_urgency, classify_emergency
from .serializers import SOSAnalysisInputSerializer, SOSAnalysisOutputSerializer


class AnalyzeSOSView(APIView):
    """
    Analyze an SOS request for urgency and classification.
    
    POST /intelligence/analyze/
    
    Uses hybrid analysis (LLM + rule-based fallback) by default.
    Pass use_llm=false to force rule-based only.
    """
    
    def post(self, request):
        """
        Analyze SOS data with hybrid LLM + rule-based approach.
        
        Accepts:
        - Raw SOS data (description, silent_mode, etc.)
        - SOS ID to fetch and analyze existing request
        - use_llm param (default true) to control LLM usage
        """
        
        # Validate input
        input_serializer = SOSAnalysisInputSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(
                input_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = input_serializer.validated_data
        use_llm = data.get('use_llm', True)
        
        # If SOS ID provided, fetch the SOS data
        if 'sos_id' in data and data['sos_id']:
            try:
                from sos.models import SOSRequest
                sos = SOSRequest.objects.get(id=data['sos_id'])
                analysis_data = {
                    'silent_mode': sos.silent_mode,
                    'description': sos.get_combined_description(),
                    'created_at': sos.created_at,
                    'latitude': float(sos.latitude),
                    'longitude': float(sos.longitude),
                    'is_bystander_report': sos.is_bystander_report,
                    'victim_condition': sos.victim_condition,
                    'estimated_victims': sos.estimated_victims,
                    'card_urgency_boost': sos.selected_card.urgency_boost if sos.selected_card else 0,
                }
            except SOSRequest.DoesNotExist:
                return Response(
                    {"error": f"SOS request {data['sos_id']} not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Use provided data
            analysis_data = {
                'silent_mode': data.get('silent_mode', False),
                'description': data.get('description', ''),
                'created_at': data.get('created_at'),
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
            }
        
        # Run hybrid analysis (LLM + fallback)
        result = analyze_sos_hybrid(analysis_data, use_llm=use_llm)
        
        # Validate output  
        output_serializer = SOSAnalysisOutputSerializer(result)
        
        return Response(output_serializer.data)


class AnalyzeSOSRuleBasedView(APIView):
    """
    Rule-based only analysis (no LLM).
    
    POST /intelligence/analyze-rules/
    
    Faster, no API calls, works offline.
    """
    
    def post(self, request):
        """Analyze SOS data using only rule-based logic."""
        
        input_serializer = SOSAnalysisInputSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(
                input_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = input_serializer.validated_data
        analysis_data = {
            'silent_mode': data.get('silent_mode', False),
            'description': data.get('description', ''),
            'created_at': data.get('created_at'),
        }
        
        result = analyze_sos(analysis_data)
        output_serializer = SOSAnalysisOutputSerializer(result)
        
        return Response(output_serializer.data)


class UrgencyOnlyView(APIView):
    """
    Calculate urgency score only (lightweight).
    
    POST /intelligence/urgency/
    """
    
    def post(self, request):
        """Calculate urgency score for given SOS data."""
        
        input_serializer = SOSAnalysisInputSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(
                input_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = calculate_urgency(input_serializer.validated_data)
        return Response(result)


class ClassifyOnlyView(APIView):
    """
    Classify emergency type only (lightweight).
    
    POST /intelligence/classify/
    """
    
    def post(self, request):
        """Classify emergency type for given SOS data."""
        
        input_serializer = SOSAnalysisInputSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(
                input_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = classify_emergency(input_serializer.validated_data)
        return Response(result)
