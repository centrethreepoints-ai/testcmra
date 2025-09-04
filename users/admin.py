"""
Admin interface for users application.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Interface d'administration pour le modèle User."""
    
    list_display = (
        'email', 
        'first_name', 
        'last_name', 
        'role', 
        'company', 
        'is_active', 
        'date_joined',
        'mfa_status',
        'user_actions'
    )
    list_filter = (
        'role', 
        'company', 
        'is_active', 
        'is_staff', 
        'is_superuser',
        'date_joined',
        'mfa_enabled'
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    list_per_page = 25
    date_hierarchy = 'date_joined'
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'phone')
        }),
        (_('Company & Role'), {
            'fields': ('company', 'role')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined')
        }),
        (_('Security'), {
            'fields': ('mfa_enabled', 'mfa_secret'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 
                'first_name', 
                'last_name', 
                'phone',
                'password1', 
                'password2', 
                'role', 
                'company',
                'is_active',
                'is_staff'
            ),
        }),
    )
    
    readonly_fields = (
        'last_login', 
        'date_joined', 
        'created_at', 
        'updated_at'
    )
    
    # Add custom CSS for better UI
    class Media:
        css = {
            'all': ('admin/css/users-admin.css',)
        }
    
    def get_queryset(self, request):
        """Filtrer les utilisateurs selon les permissions de l'admin."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Les non-superusers ne voient que les utilisateurs de leur société
        if hasattr(request.user, 'company') and request.user.company:
            return qs.filter(company=request.user.company)
        return qs.none()
    
    def get_fieldsets(self, request, obj=None):
        """Customize fieldsets based on user permissions."""
        fieldsets = super().get_fieldsets(request, obj)
        
        # Remove security section for non-superusers
        if not request.user.is_superuser and obj:
            fieldsets = tuple(fs for fs in fieldsets if fs[0] != _('Security'))
            
        return fieldsets
    
    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly based on user permissions."""
        readonly = list(super().get_readonly_fields(request, obj))
        
        # Non-superusers cannot change company of existing users
        if not request.user.is_superuser and obj:
            readonly.extend(['company', 'email'])
            
        return readonly
    
    def mfa_status(self, obj):
        """Display MFA status with colored indicators."""
        if obj.mfa_enabled:
            return format_html(
                '<span style="color: green;">✓ Enabled</span>'
            )
        return format_html(
            '<span style="color: orange;">○ Disabled</span>'
        )
    mfa_status.short_description = 'MFA Status'
    mfa_status.admin_order_field = 'mfa_enabled'
    
    def user_actions(self, obj):
        """Add quick action buttons."""
        if obj.pk:
            return format_html(
                '<a class="button" href="{}">View</a>&nbsp;'
                '<a class="button" href="{}" style="background-color: #ffc107;">Edit</a>',
                reverse('admin:users_user_change', args=[obj.pk]),
                reverse('admin:users_user_change', args=[obj.pk])
            )
        return ''
    user_actions.short_description = 'Actions'
    user_actions.allow_tags = True
    
    def save_model(self, request, obj, form, change):
        """Custom save behavior."""
        # Auto-assign company for non-superusers
        if not request.user.is_superuser and not change:
            if hasattr(request.user, 'company'):
                obj.company = request.user.company
        super().save_model(request, obj, form, change)
    
    def has_change_permission(self, request, obj=None):
        """Custom permission check."""
        if obj is None:
            return True
        
        # Superusers can change anyone
        if request.user.is_superuser:
            return True
            
        # Users can only change users from their own company
        if hasattr(request.user, 'company') and obj.company == request.user.company:
            return True
            
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Custom delete permission."""
        # Don't allow users to delete themselves
        if obj and obj == request.user:
            return False
        return super().has_delete_permission(request, obj)
    
    # Optional: Add custom actions
    actions = ['activate_users', 'deactivate_users']
    
    def activate_users(self, request, queryset):
        """Activate selected users."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request, 
            f'{updated} user(s) were successfully activated.'
        )
    activate_users.short_description = "Activate selected users"
    
    def deactivate_users(self, request, queryset):
        """Deactivate selected users."""
        # Prevent deactivating oneself
        queryset = queryset.exclude(pk=request.user.pk)
        updated = queryset.update(is_active=False)
        self.message_user(
            request, 
            f'{updated} user(s) were successfully deactivated.'
        )
    deactivate_users.short_description = "Deactivate selected users"

# Optional: Add custom filters
class CompanyFilter(admin.SimpleListFilter):
    title = _('Company')
    parameter_name = 'company'
    
    def lookups(self, request, model_admin):
        # Only show companies relevant to the current user
        if request.user.is_superuser:
            companies = User.objects.exclude(company__isnull=True).values_list(
                'company', flat=True
            ).distinct()
        else:
            companies = [request.user.company] if hasattr(request.user, 'company') else []
            
        return [(company, company) for company in companies if company]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(company=self.value())
        return queryset