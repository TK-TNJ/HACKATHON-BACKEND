from django.db.models.signals import post_save
from django.dispatch import receiver
from sos.models import SOSRequest
from .services import FCMService
import threading

@receiver(post_save, sender=SOSRequest)
def notify_responders_on_sos(sender, instance, created, **kwargs):
    """
    Trigger notification when a new SOS is created.
    """
    if created:
        # Run in a separate thread to avoid blocking the response
        # In production, use Celery for this
        
        # 1. Send FCM Alert to Responders
        threading.Thread(
            target=FCMService.send_critical_alert,
            args=(instance.id, instance.latitude, instance.longitude)
        ).start()
        
        # 2. Send SMS to Emergency Contacts
        # MOVED TO FRONTEND: The mobile app will send SMS directly to contacts.
        # This implementation strategy was chosen to reduce backend cost and dependencies.
