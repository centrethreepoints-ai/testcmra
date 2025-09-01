"""
Admin interface for users application.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Interface d'administration pour le modèle User."""
    
    list_display = ('email', 'first_name', 'last_name', 'role', 'company', 'is_active', 'date_joined')
    list_filter = ('role', 'company', 'is_active', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Informations personnelles'), {
            'fields': ('first_name', 'last_name', 'phone')
        }),
        (_('Permissions'), {
            'fields': ('role', 'company', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        (_('Dates importantes'), {
            'fields': ('last_login', 'date_joined')
        }),
        (_('MFA'), {
            'fields': ('mfa_enabled', 'mfa_secret'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'role', 'company'),
        }),
    )
    
    readonly_fields = ('last_login', 'date_joined', 'created_at', 'updated_at')
    
    def get_queryset(self, request):
        """Filtrer les utilisateurs selon les permissions de l'admin."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Les non-superusers ne voient que les utilisateurs de leur société
        if hasattr(request.user, 'company') and request.user.company:
            return qs.filter(company=request.user.company)
        return qs.none()
