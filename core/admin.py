"""
Admin interface for core application.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    ApprovalWorkflow, ApprovalRequest, ApprovalLog, 
    DashboardWidget, Notification
)


@admin.register(ApprovalWorkflow)
class ApprovalWorkflowAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'document_type', 'amount_threshold', 'active', 'company', 'created_by'
    ]
    list_filter = ['company', 'document_type', 'active']
    search_fields = ['name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('name', 'description', 'document_type', 'company', 'created_by')
        }),
        ('Configuration', {
            'fields': ('approval_levels', 'amount_threshold')
        }),
        ('Statut', {
            'fields': ('active',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'created_by')


@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    list_display = [
        'workflow', 'document_type', 'document_id', 'current_level', 
        'total_levels', 'status', 'amount', 'company', 'created_by'
    ]
    list_filter = ['company', 'status', 'current_level', 'created_at']
    search_fields = ['workflow__name', 'notes']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Workflow', {
            'fields': ('workflow', 'company', 'created_by')
        }),
        ('Document', {
            'fields': ('document_type', 'document_id', 'amount')
        }),
        ('Niveaux', {
            'fields': ('current_level', 'total_levels')
        }),
        ('Statut', {
            'fields': ('status',)
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('workflow', 'company', 'created_by')
    
    def document_link(self, obj):
        """Afficher un lien vers le document."""
        if obj.document:
            url = reverse(f'admin:{obj.document_type}_change', args=[obj.document_id])
            return format_html('<a href="{}">{}</a>', url, obj.document)
        return '—'
    document_link.short_description = 'Document'


@admin.register(ApprovalLog)
class ApprovalLogAdmin(admin.ModelAdmin):
    list_display = [
        'approval_request', 'user', 'action', 'created_at'
    ]
    list_filter = ['action', 'created_at']
    search_fields = ['approval_request__workflow__name', 'user__username', 'notes']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Demande d\'approbation', {
            'fields': ('approval_request', 'user')
        }),
        ('Action', {
            'fields': ('action', 'notes')
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('approval_request', 'user')


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'widget_type', 'user', 'active', 'created_at'
    ]
    list_filter = ['widget_type', 'active', 'created_at']
    search_fields = ['title', 'user__username']
    ordering = ['title']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('title', 'widget_type', 'user')
        }),
        ('Position et taille', {
            'fields': ('position',)
        }),
        ('Configuration', {
            'fields': ('settings',)
        }),
        ('Statut', {
            'fields': ('active',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'user', 'notification_type', 'priority', 'read', 
        'dismissed', 'company', 'created_at'
    ]
    list_filter = [
        'company', 'notification_type', 'priority', 'read', 'dismissed', 'created_at'
    ]
    search_fields = ['title', 'message', 'user__username']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'read_at']
    
    fieldsets = (
        ('Destinataire', {
            'fields': ('user', 'company', 'created_by')
        }),
        ('Notification', {
            'fields': ('title', 'message', 'notification_type', 'priority')
        }),
        ('Action', {
            'fields': ('action_url', 'action_text')
        }),
        ('Statut', {
            'fields': ('read', 'dismissed', 'read_at')
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'company', 'created_by')
    
    def mark_as_read(self, request, queryset):
        """Marquer les notifications comme lues."""
        updated = queryset.update(read=True)
        self.message_user(request, f'{updated} notification(s) marquée(s) comme lue(s).')
    mark_as_read.short_description = 'Marquer comme lu'
    
    def mark_as_unread(self, request, queryset):
        """Marquer les notifications comme non lues."""
        updated = queryset.update(read=False, read_at=None)
        self.message_user(request, f'{updated} notification(s) marquée(s) comme non lue(s).')
    mark_as_unread.short_description = 'Marquer comme non lu'
    
    actions = [mark_as_read, mark_as_unread]
