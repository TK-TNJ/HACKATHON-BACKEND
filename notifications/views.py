from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import FCMService
import logging

logger = logging.getLogger(__name__)

class RegisterTokenView(APIView):
    """
    Endpoint for frontend to register a device token and subscribe to topics.
    """
    def post(self, request):
        token = request.data.get('token')
        
        if not token:
            return Response({"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Subscribe the token to the 'responders' topic
        # In a real app, you might check if the user is actually a responder first.
        success = FCMService.subscribe_to_topic([token], 'responders')
        
        if success:
            return Response({"message": "Token registered and subscribed to responders"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Failed to subscribe to topic"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
