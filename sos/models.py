"""
SOS Models - Emergency Request Core

This module defines the SOSRequest model which is the core entity
representing an emergency situation that needs response.
"""

from django.db import models
from accounts.models import UserProfile


class SOSRequest(models.Model):
    """
    Core emergency request entity.
    
    Represents a single emergency situation initiated by a user.
    One SOS = One emergency event.
    
    Note: Urgency calculation and responder assignment are handled
    by the intelligence and response apps respectively.
    """
    
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('analyzing', 'Analyzing'),
        ('assigned', 'Assigned to Responder'),
        ('in_progress', 'Response In Progress'),
        ('resolved', 'Resolved'),
        ('cancelled', 'Cancelled'),
    ]
    
    # User who initiated the SOS
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='sos_requests',
        help_text="User who created this SOS request"
    )
    
    # Location of the emergency
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Latitude of emergency location"
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Longitude of emergency location"
    )
    
    # Location description (optional, for low connectivity scenarios)
    location_description = models.TextField(
        blank=True,
        null=True,
        help_text="Text description of location if GPS is unavailable"
    )
    
    # Silent mode - for situations where user cannot speak/make noise
    silent_mode = models.BooleanField(
        default=False,
        help_text="True if user activated SOS silently (cannot speak)"
    )
    
    # Optional description or keywords
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional emergency description or keywords"
    )
    
    # Current status of the SOS
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='created',
        help_text="Current lifecycle status of the SOS"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when SOS was resolved"
    )
    
    class Meta:
        verbose_name = "SOS Request"
        verbose_name_plural = "SOS Requests"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"SOS #{self.id} - {self.status} ({self.user.supabase_user_id})"
    
    def mark_resolved(self):
        """
        Mark this SOS as resolved and set resolution timestamp.
        """
        from django.utils import timezone
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        self.save()
