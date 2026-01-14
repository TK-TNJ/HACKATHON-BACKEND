"""
SOS Admin Configuration
"""

from django.contrib import admin
from .models import SOSRequest


@admin.register(SOSRequest)
class SOSRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'silent_mode', 'created_at']
    list_filter = ['status', 'silent_mode', 'created_at']
    search_fields = ['user__supabase_user_id', 'description']
    readonly_fields = ['created_at', 'updated_at', 'resolved_at']
    ordering = ['-created_at']
