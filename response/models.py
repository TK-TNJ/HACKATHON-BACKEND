"""
Response Models - Responder Assignment and Coordination

This module defines models for tracking which responders
are assigned to which SOS requests.
"""

from django.db import models
from accounts.models import ResponderProfile
from sos.models import SOSRequest


class ResponderAssignment(models.Model):
    """
    Tracks assignment of responders to SOS requests.
    
    One SOS can have one primary responder (MVP).
    Future versions may support multiple responders.
    """
    
    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('accepted', 'Accepted by Responder'),
        ('en_route', 'En Route'),
        ('on_scene', 'On Scene'),
        ('completed', 'Completed'),
        ('declined', 'Declined'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Link to SOS request
    sos = models.ForeignKey(
        SOSRequest,
        on_delete=models.CASCADE,
        related_name='assignments',
        help_text="The SOS request this assignment is for"
    )
    
    # Link to responder
    responder = models.ForeignKey(
        ResponderProfile,
        on_delete=models.CASCADE,
        related_name='assignments',
        help_text="The responder assigned to this SOS"
    )
    
    # Assignment status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='assigned',
        help_text="Current status of this assignment"
    )
    
    # Timestamps
    assigned_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Notes from responder
    responder_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notes from responder about the response"
    )
    
    class Meta:
        verbose_name = "Responder Assignment"
        verbose_name_plural = "Responder Assignments"
        ordering = ['-assigned_at']
        # Ensure one responder isn't assigned to same SOS multiple times
        unique_together = ['sos', 'responder']
    
    def __str__(self):
        return f"Assignment: SOS #{self.sos.id} -> {self.responder}"
    
    def accept(self):
        """Mark assignment as accepted by responder."""
        from django.utils import timezone
        self.status = 'accepted'
        self.accepted_at = timezone.now()
        self.save()
        
        # Update SOS status
        self.sos.status = 'assigned'
        self.sos.save()
    
    def complete(self, notes=None):
        """Mark assignment as completed."""
        from django.utils import timezone
        self.status = 'completed'
        self.completed_at = timezone.now()
        if notes:
            self.responder_notes = notes
        self.save()


class AuthorityEscalation(models.Model):
    """
    Tracks escalations to authorities (police, fire, medical).
    
    For MVP, this is a simple record. In production, this would
    integrate with actual emergency services.
    """
    
    AUTHORITY_TYPES = [
        ('police', 'Police'),
        ('fire', 'Fire Department'),
        ('medical', 'Medical/Ambulance'),
        ('other', 'Other Authority'),
    ]
    
    # Link to SOS
    sos = models.ForeignKey(
        SOSRequest,
        on_delete=models.CASCADE,
        related_name='escalations',
        help_text="The SOS request that was escalated"
    )
    
    # Type of authority
    authority_type = models.CharField(
        max_length=20,
        choices=AUTHORITY_TYPES,
        help_text="Type of authority escalated to"
    )
    
    # Reason for escalation
    reason = models.TextField(
        help_text="Reason for escalating to authorities"
    )
    
    # Timestamps
    escalated_at = models.DateTimeField(auto_now_add=True)
    
    # Mock: In production, this would be a case/ticket ID from the authority
    authority_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Reference ID from the authority (mock for MVP)"
    )
    
    class Meta:
        verbose_name = "Authority Escalation"
        verbose_name_plural = "Authority Escalations"
        ordering = ['-escalated_at']
    
    def __str__(self):
        return f"Escalation: SOS #{self.sos.id} -> {self.authority_type}"
