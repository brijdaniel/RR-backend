from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _


from .models import *


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ['username']
    list_display = ['username', 'is_staff', 'allow_networking', 'followers_count', 'following_count']

    fieldsets = (
        (_('Personal Info'), {'fields': ('username',)}),
        (_('Networking'), {'fields': ('allow_networking', 'followers_count', 'following_count')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username'),
        }),
    )

    search_fields = ['username']
    readonly_fields = ['followers_count', 'following_count']


@admin.register(Checklist)
class ChecklistAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'score', 'completed', 'created_at']
    list_filter = ['completed', 'created_at']
    search_fields = ['user__username']

@admin.register(Regret)
class RegretAdmin(admin.ModelAdmin):
    list_display = ['id', 'checklist', 'description', 'success', 'created_at']
    list_filter = ['success', 'created_at']
    search_fields = ['description', 'checklist__user__username']

@admin.register(Network)
class NetworkAdmin(admin.ModelAdmin):
    list_display = ['id', 'follower', 'following', 'created_at']
    list_filter = ['created_at']
    search_fields = ['follower__username', 'following__username']
    readonly_fields = ['created_at']
