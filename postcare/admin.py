"""
Postcare Admin Configuration
"""

from django.contrib import admin
from .models import IncidentFeedback, FollowUp


@admin.register(IncidentFeedback)
class IncidentFeedbackAdmin(admin.ModelAdmin):
    list_display = ['id', 'sos', 'rating', 'was_helpful', 'would_recommend', 'submitted_at']
    list_filter = ['rating', 'was_helpful', 'would_recommend', 'submitted_at']
    search_fields = ['sos__id', 'comment']
    readonly_fields = ['submitted_at']
    ordering = ['-submitted_at']


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ['id', 'sos', 'is_safe', 'needs_support', 'followup_time']
    list_filter = ['is_safe', 'needs_support', 'followup_time']
    search_fields = ['sos__id', 'notes']
    readonly_fields = ['followup_time']
    ordering = ['-followup_time']
