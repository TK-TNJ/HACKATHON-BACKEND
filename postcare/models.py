"""
Postcare Models - Feedback and Follow-up Tracking

This module defines models for post-incident care, including
feedback from users and follow-up check-ins.
"""

from django.db import models
from sos.models import SOSRequest


class IncidentFeedback(models.Model):
    """
    Feedback submitted after an SOS incident is resolved.
    
    Captures user satisfaction and comments about the response.
    Used for responder reputation updates and system improvement.
    """
    
    # Link to the resolved SOS
    sos = models.OneToOneField(
        SOSRequest,
        on_delete=models.CASCADE,
        related_name='feedback',
        help_text="The SOS request this feedback is for"
    )
    
    # Rating (1-5 stars)
    rating = models.IntegerField(
        help_text="Rating from 1-5 (1=poor, 5=excellent)"
    )
    
    # Optional comment
    comment = models.TextField(
        blank=True,
        null=True,
        help_text="Optional feedback comment"
    )
    
    # Was the response helpful?
    was_helpful = models.BooleanField(
        default=True,
        help_text="Did the response help resolve the emergency?"
    )
    
    # Would user recommend LifeLink?
    would_recommend = models.BooleanField(
        default=True,
        help_text="Would user recommend LifeLink to others?"
    )
    
    # Timestamp
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Incident Feedback"
        verbose_name_plural = "Incident Feedback"
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"Feedback for SOS #{self.sos.id}: {self.rating}/5"
    
    def save(self, *args, **kwargs):
        """Validate rating is between 1 and 5."""
        if self.rating < 1:
            self.rating = 1
        elif self.rating > 5:
            self.rating = 5
        super().save(*args, **kwargs)


class FollowUp(models.Model):
    """
    Follow-up check-in after an incident.
    
    Allows users to confirm they are safe and provides
    continuity of care after the immediate emergency.
    """
    
    # Link to the SOS
    sos = models.ForeignKey(
        SOSRequest,
        on_delete=models.CASCADE,
        related_name='followups',
        help_text="The SOS request this follow-up is for"
    )
    
    # Is the user safe now?
    is_safe = models.BooleanField(
        help_text="Is the user currently safe?"
    )
    
    # Follow-up notes
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes from follow-up check-in"
    )
    
    # Does user need additional support?
    needs_support = models.BooleanField(
        default=False,
        help_text="Does user need additional support or resources?"
    )
    
    # Type of support needed (if any)
    support_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Type of additional support needed (if any)"
    )
    
    # Timestamp
    followup_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Follow-Up Check-in"
        verbose_name_plural = "Follow-Up Check-ins"
        ordering = ['-followup_time']
    
    def __str__(self):
        status = "Safe" if self.is_safe else "Needs attention"
        return f"Follow-up for SOS #{self.sos.id}: {status}"
