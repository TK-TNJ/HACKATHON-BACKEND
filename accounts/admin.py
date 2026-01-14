"""
Accounts Admin Configuration
"""

from django.contrib import admin
from .models import UserProfile, ResponderProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['supabase_user_id', 'role', 'trust_score', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['supabase_user_id']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ResponderProfile)
class ResponderProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_available', 'reputation_score', 'created_at']
    list_filter = ['is_available', 'created_at']
    search_fields = ['user__supabase_user_id']
    readonly_fields = ['created_at', 'updated_at']
