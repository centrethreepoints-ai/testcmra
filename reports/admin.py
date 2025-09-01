"""
Admin interface for reports application.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    ReportSchedule, CashFlowStatement, AgingReport, ProfitLossStatement
)


@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'report_type', 'frequency', 'active', 'company', 'created_by'
    ]
    list_filter = ['company', 'report_type', 'frequency', 'active']
    search_fields = ['name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at', 'last_run', 'next_run']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('name', 'description', 'report_type', 'company', 'created_by')
        }),
        ('Planification', {
            'fields': ('frequency', 'day_of_week', 'day_of_month', 'month')
        }),
        ('Destinataires', {
            'fields': ('recipients', 'cc_recipients')
        }),
        ('Paramètres', {
            'fields': ('parameters',)
        }),
        ('Statut', {
            'fields': ('active', 'last_run', 'next_run')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'created_by')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nouvelle planification
            obj.created_by = request.user
            obj.next_run = obj.get_next_run_date()
        super().save_model(request, obj, form, change)


@admin.register(CashFlowStatement)
class CashFlowStatementAdmin(admin.ModelAdmin):
    list_display = [
        'period_type', 'start_date', 'end_date', 'operating_cash_flow',
        'investing_cash_flow', 'financing_cash_flow', 'net_cash_change',
        'closing_cash', 'company'
    ]
    list_filter = ['company', 'period_type', 'start_date', 'end_date']
    search_fields = ['company__name']
    ordering = ['-end_date']
    readonly_fields = ['created_at', 'net_cash_change', 'closing_cash']
    
    fieldsets = (
        ('Période', {
            'fields': ('period_type', 'start_date', 'end_date', 'company', 'created_by')
        }),
        ('Flux d\'exploitation', {
            'fields': ('operating_cash_flow',)
        }),
        ('Flux d\'investissement', {
            'fields': ('investing_cash_flow',)
        }),
        ('Flux de financement', {
            'fields': ('financing_cash_flow',)
        }),
        ('Variation de trésorerie', {
            'fields': ('net_cash_change',)
        }),
        ('Trésorerie', {
            'fields': ('opening_cash', 'closing_cash')
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'created_by')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nouveau rapport
            obj.created_by = request.user
        obj.calculate_net_cash_change()
        obj.calculate_closing_cash()
        super().save_model(request, obj, form, change)


@admin.register(AgingReport)
class AgingReportAdmin(admin.ModelAdmin):
    list_display = [
        'report_type', 'report_date', 'current_amount', 'days_30_amount',
        'days_60_amount', 'days_90_amount', 'days_120_amount', 'over_120_amount',
        'total_amount', 'company'
    ]
    list_filter = ['company', 'report_type', 'report_date']
    search_fields = ['company__name']
    ordering = ['-report_date']
    readonly_fields = ['created_at', 'total_amount']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('report_type', 'report_date', 'company', 'created_by')
        }),
        ('Montants par période', {
            'fields': ('current_amount', 'days_30_amount', 'days_60_amount', 'days_90_amount', 'days_120_amount', 'over_120_amount')
        }),
        ('Total', {
            'fields': ('total_amount',)
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'created_by')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nouveau rapport
            obj.created_by = request.user
        obj.calculate_total()
        super().save_model(request, obj, form, change)


@admin.register(ProfitLossStatement)
class ProfitLossStatementAdmin(admin.ModelAdmin):
    list_display = [
        'period_type', 'start_date', 'end_date', 'revenue', 'cost_of_sales',
        'operating_profit', 'net_profit', 'company'
    ]
    list_filter = ['company', 'period_type', 'start_date', 'end_date']
    search_fields = ['company__name']
    ordering = ['-end_date']
    readonly_fields = [
        'created_at', 'total_income', 'total_expenses', 'operating_profit',
        'financial_result', 'exceptional_result', 'net_profit'
    ]
    
    fieldsets = (
        ('Période', {
            'fields': ('period_type', 'start_date', 'end_date', 'company', 'created_by')
        }),
        ('Produits', {
            'fields': ('revenue', 'other_income', 'total_income')
        }),
        ('Charges', {
            'fields': ('cost_of_sales', 'operating_expenses', 'financial_expenses', 'exceptional_expenses', 'total_expenses')
        }),
        ('Résultats', {
            'fields': ('operating_profit', 'financial_result', 'exceptional_result', 'net_profit')
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'created_by')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nouveau rapport
            obj.created_by = request.user
        obj.calculate_totals()
        super().save_model(request, obj, form, change)
