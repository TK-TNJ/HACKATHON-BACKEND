"""
Intelligence Views - API endpoints for emergency analysis.

These endpoints provide the "brain" functionality for analyzing
SOS requests and determining urgency/classification.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .services import analyze_sos, calculate_urgency, classify_emergency
from .serializers import SOSAnalysisInputSerializer, SOSAnalysisOutputSerializer


class AnalyzeSOSView(APIView):
    """
    Analyze an SOS request for urgency and classification.
    
    POST /intelligence/analyze/
    
    This is the main intelligence endpoint. Send SOS data and
    receive urgency score, severity level, and emergency classification.
    """
    
    def post(self, request):
        """
        Analyze SOS data and return intelligence results.
        
        Can accept either:
        1. Raw SOS data (latitude, longitude, silent_mode, description)
        2. SOS ID to fetch and analyze existing request
        """
        
        # Validate input
        input_serializer = SOSAnalysisInputSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(
                input_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = input_serializer.validated_data
        
        # If SOS ID provided, fetch the SOS data
        if 'sos_id' in data and data['sos_id']:
            try:
                from sos.models import SOSRequest
                sos = SOSRequest.objects.get(id=data['sos_id'])
                analysis_data = {
                    'silent_mode': sos.silent_mode,
                    'description': sos.description,
                    'created_at': sos.created_at,
                    'latitude': float(sos.latitude),
                    'longitude': float(sos.longitude),
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
        
        # Run analysis
        result = analyze_sos(analysis_data)
        
        # Validate output  
        output_serializer = SOSAnalysisOutputSerializer(result)
        
        return Response(output_serializer.data)


class UrgencyOnlyView(APIView):
    """
    Calculate urgency score only (lightweight analysis).
    
    POST /intelligence/urgency/
    
    Returns just the urgency score and severity level.
    Useful for quick checks without full classification.
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
    Classify emergency type only (lightweight analysis).
    
    POST /intelligence/classify/
    
    Returns just the emergency classification.
    Useful for quick categorization without urgency calculation.
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
