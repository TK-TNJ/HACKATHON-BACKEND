"""
SOS Admin Configuration
"""

from django.contrib import admin
from .models import SOSRequest, EmergencyCard


@admin.register(EmergencyCard)
class EmergencyCardAdmin(admin.ModelAdmin):
    list_display = ['icon', 'name', 'code', 'category', 'urgency_boost', 'display_order', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'code']
    ordering = ['display_order', 'name']
    list_editable = ['display_order', 'is_active', 'urgency_boost']


@admin.register(SOSRequest)
class SOSRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'selected_card', 'is_bystander_report', 'status', 'silent_mode', 'created_at']
    list_filter = ['status', 'silent_mode', 'is_bystander_report', 'selected_card', 'created_at']
    search_fields = ['user__supabase_user_id', 'description', 'additional_details']
    readonly_fields = ['created_at', 'updated_at', 'resolved_at']
    ordering = ['-created_at']

