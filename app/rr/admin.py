from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _


from .models import *


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ['username']
    list_display = ['username', 'is_staff']

    fieldsets = (
        (_('Personal Info'), {'fields': ('username',)}),
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


admin.site.register(Checklist)
admin.site.register(Regret)
