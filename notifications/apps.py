from django.apps import AppConfig
import firebase_admin
from firebase_admin import credentials
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)

class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'

    def ready(self):
        # Initialize Firebase Admin SDK
        try:
            cred_path = os.path.join(settings.BASE_DIR, 'backend', 'serviceAccountKey.json')
            if not firebase_admin._apps:
                if os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                    logger.info("Firebase Admin SDK initialized successfully")
                else:
                    logger.warning(f"Firebase credentials not found at {cred_path}. Notifications will not work.")
            
            # Register signals
            import notifications.signals
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {str(e)}")
