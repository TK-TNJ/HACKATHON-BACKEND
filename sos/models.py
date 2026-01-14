"""
SOS Models - Emergency Request Core

This module defines the SOSRequest model which is the core entity
representing an emergency situation that needs response.
Also includes EmergencyCard for quick-tap emergency selection.
"""

from django.db import models
from accounts.models import UserProfile


class EmergencyCard(models.Model):
    """
    Pre-defined emergency types for quick one-tap selection.
    
    These cards appear on the app home screen, allowing users to
    quickly indicate their emergency type without typing.
    """
    
    CATEGORY_CHOICES = [
        ('medical', 'Medical Emergency'),
        ('safety', 'Safety/Security'),
        ('accident', 'Accident'),
        ('emotional', 'Emotional/Mental Health'),
    ]
    
    # Unique identifier for the card
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique code like 'heart_attack', 'road_accident'"
    )
    
    # Display name
    name = models.CharField(
        max_length=100,
        help_text="Display name like 'Heart Attack', 'Road Accident'"
    )
    
    # Emoji icon for visual identification
    icon = models.CharField(
        max_length=10,
        help_text="Emoji icon for the card, e.g., 🫀, 🚗"
    )
    
    # Category for classification
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        help_text="Emergency category for routing"
    )
    
    # Urgency boost when this card is selected
    urgency_boost = models.IntegerField(
        default=20,
        help_text="Points added to base urgency score (0-50)"
    )
    
    # Keywords for intelligence matching
    keywords = models.JSONField(
        default=list,
        help_text="Keywords associated with this emergency type"
    )
    
    # Display order in the app
    display_order = models.IntegerField(
        default=0,
        help_text="Order in which cards appear (lower = first)"
    )
    
    # Whether card is currently active
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this card is shown to users"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Emergency Card"
        verbose_name_plural = "Emergency Cards"
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return f"{self.icon} {self.name}"


class SOSRequest(models.Model):
    """
    Core emergency request entity.
    
    Represents a single emergency situation initiated by a user.
    One SOS = One emergency event.
    
    Supports:
    - Quick card selection for common emergencies
    - Bystander reporting (someone reporting for another person)
    - Additional details text input
    
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
    
    VICTIM_CONDITION_CHOICES = [
        ('conscious', 'Conscious and responsive'),
        ('semi_conscious', 'Semi-conscious / Confused'),
        ('unconscious', 'Unconscious / Unresponsive'),
        ('unknown', 'Unknown / Cannot determine'),
    ]
    
    # User who initiated the SOS
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='sos_requests',
        help_text="User who created this SOS request"
    )
    
    # ========== QUICK CARD SELECTION ==========
    # Selected emergency card (if user tapped a quick card)
    selected_card = models.ForeignKey(
        EmergencyCard,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sos_requests',
        help_text="Emergency card selected by user (quick-tap)"
    )
    
    # Additional details beyond the card (text area)
    additional_details = models.TextField(
        blank=True,
        null=True,
        help_text="Additional context not covered by the selected card"
    )
    
    # ========== BYSTANDER REPORTING ==========
    # Is this a report for someone else?
    is_bystander_report = models.BooleanField(
        default=False,
        help_text="True if reporter is a bystander reporting for someone else"
    )
    
    # Victim's apparent condition (for bystander reports)
    victim_condition = models.CharField(
        max_length=20,
        choices=VICTIM_CONDITION_CHOICES,
        default='unknown',
        blank=True,
        help_text="Victim's apparent condition (for bystander reports)"
    )
    
    # Estimated number of victims (for multi-casualty events)
    estimated_victims = models.IntegerField(
        default=1,
        help_text="Estimated number of people needing help"
    )
    
    # ========== LOCATION ==========
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
    
    # ========== LEGACY FIELDS (still supported) ==========
    # Silent mode - for situations where user cannot speak/make noise
    silent_mode = models.BooleanField(
        default=False,
        help_text="True if user activated SOS silently (cannot speak)"
    )
    
    # Optional description or keywords (legacy, use additional_details for new)
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional emergency description or keywords"
    )
    
    # ========== STATUS & TIMESTAMPS ==========
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='created',
        help_text="Current lifecycle status of the SOS"
    )
    
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
        card_info = f" [{self.selected_card.name}]" if self.selected_card else ""
        bystander_info = " (BYSTANDER)" if self.is_bystander_report else ""
        return f"SOS #{self.id}{card_info}{bystander_info} - {self.status}"
    
    def mark_resolved(self):
        """Mark this SOS as resolved and set resolution timestamp."""
        from django.utils import timezone
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        self.save()
    
    def get_combined_description(self):
        """
        Get combined description from card keywords + additional details.
        Used by intelligence system for analysis.
        """
        parts = []
        
        # Add card name and keywords
        if self.selected_card:
            parts.append(self.selected_card.name)
            if self.selected_card.keywords:
                parts.extend(self.selected_card.keywords)
        
        # Add additional details
        if self.additional_details:
            parts.append(self.additional_details)
        
        # Add legacy description
        if self.description:
            parts.append(self.description)
        
        return ' '.join(parts)

