"""
Accounts Models - User and Responder Profiles

This module defines the core profile models for LifeLink.
Note: Authentication is handled by Supabase externally.
Django only stores profile and system data.
"""

from django.db import models


class UserProfile(models.Model):
    """
    User profile linked to Supabase authentication.
    
    Stores additional user data that isn't handled by Supabase Auth,
    including role information and trust metrics.
    """
    
    ROLE_CHOICES = [
        ('user', 'Regular User'),
        ('responder', 'Emergency Responder'),
    ]
    
    # Unique identifier from Supabase Auth
    supabase_user_id = models.CharField(
        max_length=255, 
        unique=True,
        help_text="UUID from Supabase Auth"
    )
    
    # User role determines access and capabilities
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='user',
        help_text="User role in the system"
    )
    
    # Trust score for prioritization and verification
    trust_score = models.IntegerField(
        default=50,
        help_text="Trust score from 0-100, affects SOS prioritization"
    )
    
    # Custom Auth Fields (Requested by User)
    email = models.EmailField(
        unique=True,
        null=True, # Allow null for existing users or migration
        blank=True,
        help_text="User email for custom login"
    )
    password = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text="Hashed password for custom login"
    )

    # Emergency Contacts
    emergency_contacts = models.JSONField(
        default=list,
        blank=True,
        help_text="List of emergency contacts (max 3)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.supabase_user_id} ({self.role})"


class ResponderProfile(models.Model):
    """
    Extended profile for emergency responders.
    
    Contains responder-specific data like skills, availability,
    and reputation metrics used for matching with SOS requests.
    """
    
    # Link to the base user profile
    user = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='responder_profile',
        help_text="Base user profile for this responder"
    )
    
    # Skills as JSON list (e.g., ["first_aid", "cpr", "firefighting"])
    skills = models.JSONField(
        default=list,
        help_text="List of responder skills/certifications"
    )
    
    # Availability status for matching
    is_available = models.BooleanField(
        default=True,
        help_text="Whether responder is currently available for assignments"
    )
    
    # Reputation based on completed responses and feedback
    reputation_score = models.IntegerField(
        default=50,
        help_text="Reputation score from 0-100, based on response history"
    )
    
    # Location for proximity matching (optional)
    last_known_latitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True
    )
    last_known_longitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Responder Profile"
        verbose_name_plural = "Responder Profiles"
        ordering = ['-reputation_score']
    
    def __str__(self):
        return f"Responder: {self.user.supabase_user_id}"
