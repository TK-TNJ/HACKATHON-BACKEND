import logging
from firebase_admin import messaging
from typing import Optional, Dict
import os

logger = logging.getLogger(__name__)

class FCMService:
    """
    Service for sending Firebase Cloud Messaging notifications.
    """
    
    @staticmethod
    def send_to_topic(topic: str, title: str, body: str, data: Optional[Dict[str, str]] = None) -> bool:
        """
        Send a notification to a specific topic.
        
        Args:
            topic: The topic name (e.g., 'all_responders')
            title: Notification title
            body: Notification body text
            data: Optional dictionary of data payload (all values must be strings)
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            # Ensure data values are strings (FCM requirement)
            if data:
                data = {k: str(v) for k, v in data.items()}
            
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data,
                topic=topic,
            )
            
            response = messaging.send(message)
            logger.info(f"Successfully sent message to topic {topic}: {response}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification to topic {topic}: {str(e)}")
            return False

    @staticmethod
    def subscribe_to_topic(tokens: list, topic: str) -> bool:
        """
        Subscribe a list of tokens to a topic.
        """
        try:
            response = messaging.subscribe_to_topic(tokens, topic)
            logger.info(f"Subscribed {response.success_count} tokens to {topic}")
            return True
        except Exception as e:
            logger.error(f"Failed to subscribe to topic {topic}: {str(e)}")
            return False

    @staticmethod
    def send_critical_alert(sos_id: int, latitude: float, longitude: float):
        """
        Send a critical alert to all responders about a new SOS.
        """
        return FCMService.send_to_topic(
            topic='responders',
            title='🚨 EMERGENCY ALERT',
            body='New SOS Request! Tap to view details.',
            data={
                'type': 'sos_alert',
                'sos_id': str(sos_id),
                'latitude': str(latitude),
                'longitude': str(longitude),
                'click_action': 'FLUTTER_NOTIFICATION_CLICK'
            }
        )


