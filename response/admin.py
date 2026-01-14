"""
Response Admin Configuration
"""

from django.contrib import admin
from .models import ResponderAssignment, AuthorityEscalation


@admin.register(ResponderAssignment)
class ResponderAssignmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'sos', 'responder', 'status', 'assigned_at']
    list_filter = ['status', 'assigned_at']
    search_fields = ['sos__id', 'responder__user__supabase_user_id']
    readonly_fields = ['assigned_at', 'accepted_at', 'completed_at']
    ordering = ['-assigned_at']


@admin.register(AuthorityEscalation)
class AuthorityEscalationAdmin(admin.ModelAdmin):
    list_display = ['id', 'sos', 'authority_type', 'escalated_at', 'authority_reference']
    list_filter = ['authority_type', 'escalated_at']
    search_fields = ['sos__id', 'authority_reference']
    readonly_fields = ['escalated_at']
    ordering = ['-escalated_at']
