"""
Admin interface for billing application.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Quote, PurchaseOrder, Invoice, CreditNote, DocumentLine, 
    Payment, PaymentAllocation, PaymentSchedule, BankReconciliation,
    EmailTemplate, EmailLog
)


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = [
        'number', 'party', 'issue_date', 'valid_until', 'total_ttc', 
        'status', 'is_converted', 'company'
    ]
    list_filter = ['company', 'status', 'is_converted', 'issue_date']
    search_fields = ['number', 'party__name']
    ordering = ['-issue_date']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('company', 'party', 'number', 'sequence_code')
        }),
        ('Dates', {
            'fields': ('issue_date', 'validity_days', 'valid_until')
        }),
        ('Montants', {
            'fields': ('total_ht', 'total_tva', 'total_ttc', 'currency', 'exchange_rate')
        }),
        ('Remises et retenues', {
            'fields': ('discount_percent', 'discount_amount', 'withholding_tax_percent', 'withholding_tax_amount')
        }),
        ('Statut', {
            'fields': ('status', 'is_converted', 'converted_to', 'converted_po')
        }),
        ('Notes et conditions', {
            'fields': ('notes', 'terms')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('party', 'company')


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = [
        'number', 'party', 'order_type', 'issue_date', 'delivery_date', 
        'total_ttc', 'status', 'company'
    ]
    list_filter = ['company', 'order_type', 'status', 'issue_date']
    search_fields = ['number', 'party__name', 'delivery_address']
    ordering = ['-issue_date']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('company', 'party', 'number', 'sequence_code', 'order_type')
        }),
        ('Dates', {
            'fields': ('issue_date', 'due_date', 'delivery_date')
        }),
        ('Livraison', {
            'fields': ('delivery_address',)
        }),
        ('Montants', {
            'fields': ('total_ht', 'total_tva', 'total_ttc', 'currency', 'exchange_rate')
        }),
        ('Remises et retenues', {
            'fields': ('discount_percent', 'discount_amount', 'withholding_tax_percent', 'withholding_tax_amount')
        }),
        ('Statut', {
            'fields': ('status', 'converted_invoice')
        }),
        ('Notes et conditions', {
            'fields': ('notes', 'terms')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('party', 'company')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        'number', 'party', 'invoice_type', 'issue_date', 'due_date', 
        'total_ttc', 'status', 'is_posted', 'company'
    ]
    list_filter = ['company', 'invoice_type', 'status', 'is_posted', 'issue_date']
    search_fields = ['number', 'party__name']
    ordering = ['-issue_date']
    readonly_fields = ['created_at', 'updated_at', 'posted_at']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('company', 'party', 'number', 'sequence_code', 'invoice_type')
        }),
        ('Références', {
            'fields': ('quote', 'purchase_order')
        }),
        ('Dates', {
            'fields': ('issue_date', 'due_date', 'payment_terms')
        }),
        ('Montants', {
            'fields': ('total_ht', 'total_tva', 'total_ttc', 'currency', 'exchange_rate')
        }),
        ('Remises et retenues', {
            'fields': ('discount_percent', 'discount_amount', 'withholding_tax_percent', 'withholding_tax_amount')
        }),
        ('Statut', {
            'fields': ('status', 'is_posted', 'posted_at')
        }),
        ('Notes et conditions', {
            'fields': ('notes', 'terms')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('party', 'company')


@admin.register(CreditNote)
class CreditNoteAdmin(admin.ModelAdmin):
    list_display = [
        'number', 'party', 'credit_type', 'original_invoice', 'issue_date', 
        'total_ttc', 'status', 'company'
    ]
    list_filter = ['company', 'credit_type', 'status', 'issue_date']
    search_fields = ['number', 'party__name', 'reason']
    ordering = ['-issue_date']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('company', 'party', 'number', 'sequence_code', 'credit_type')
        }),
        ('Facture d\'origine', {
            'fields': ('original_invoice', 'reason')
        }),
        ('Dates', {
            'fields': ('issue_date', 'due_date')
        }),
        ('Montants', {
            'fields': ('total_ht', 'total_tva', 'total_ttc', 'currency', 'exchange_rate')
        }),
        ('Remises et retenues', {
            'fields': ('discount_percent', 'discount_amount', 'withholding_tax_percent', 'withholding_tax_amount')
        }),
        ('Statut', {
            'fields': ('status',)
        }),
        ('Notes et conditions', {
            'fields': ('notes', 'terms')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('party', 'original_invoice', 'company')


@admin.register(DocumentLine)
class DocumentLineAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'document', 'quantity', 'unit_price_ht', 
        'total_line_ht', 'total_line_ttc'
    ]
    list_filter = ['tax_rate', 'created_at']
    search_fields = ['product__name', 'description']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'tax_rate')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'reference', 'party', 'payment_type', 'method', 'amount', 
        'currency', 'date', 'is_reconciled', 'company'
    ]
    list_filter = ['company', 'payment_type', 'method', 'is_reconciled', 'date']
    search_fields = ['reference', 'party__name', 'check_number', 'bank_name']
    ordering = ['-date']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('company', 'party', 'payment_type', 'method')
        }),
        ('Paiement', {
            'fields': ('amount', 'currency', 'exchange_rate', 'reference')
        }),
        ('Détails', {
            'fields': ('check_number', 'bank_name', 'value_date')
        }),
        ('Statut', {
            'fields': ('is_reconciled',)
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
        return super().get_queryset(request).select_related('party', 'company')


@admin.register(PaymentAllocation)
class PaymentAllocationAdmin(admin.ModelAdmin):
    list_display = [
        'payment', 'document', 'allocated_amount', 'reconciliation_group', 
        'created_at'
    ]
    list_filter = ['created_at']
    search_fields = ['payment__reference', 'payment__party__name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('payment', 'payment__party')


@admin.register(PaymentSchedule)
class PaymentScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'invoice', 'due_date', 'amount', 'status', 'payment'
    ]
    list_filter = ['status', 'due_date']
    search_fields = ['invoice__number', 'invoice__party__name']
    ordering = ['due_date']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Facture', {
            'fields': ('invoice',)
        }),
        ('Échéance', {
            'fields': ('due_date', 'amount', 'status')
        }),
        ('Paiement', {
            'fields': ('payment',)
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
        return super().get_queryset(request).select_related('invoice', 'invoice__party', 'payment')


@admin.register(BankReconciliation)
class BankReconciliationAdmin(admin.ModelAdmin):
    list_display = [
        'bank_account', 'statement_date', 'statement_balance', 'book_balance', 
        'difference', 'status', 'company'
    ]
    list_filter = ['company', 'status', 'statement_date']
    search_fields = ['bank_account__name', 'notes']
    ordering = ['-statement_date']
    readonly_fields = ['created_at', 'updated_at', 'difference']
    
    fieldsets = (
        ('Compte bancaire', {
            'fields': ('bank_account', 'company')
        }),
        ('Relevé', {
            'fields': ('statement_date', 'statement_balance', 'book_balance')
        }),
        ('Différence', {
            'fields': ('difference',)
        }),
        ('Statut', {
            'fields': ('status', 'reconciled')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Métadonnées', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('bank_account', 'company', 'created_by')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nouveau rapprochement
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'template_type', 'active', 'company', 'created_by'
    ]
    list_filter = ['company', 'template_type', 'active']
    search_fields = ['name', 'subject']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('name', 'template_type', 'company', 'created_by')
        }),
        ('Contenu', {
            'fields': ('subject', 'body')
        }),
        ('Variables', {
            'fields': ('available_variables',)
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


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = [
        'template', 'recipient', 'subject', 'status', 'sent_at', 
        'company', 'created_by'
    ]
    list_filter = ['company', 'status', 'sent_at', 'created_at']
    search_fields = ['recipient', 'subject', 'template__name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'sent_at']
    
    fieldsets = (
        ('Template', {
            'fields': ('template', 'company', 'created_by')
        }),
        ('Destinataire', {
            'fields': ('recipient', 'subject', 'body')
        }),
        ('Statut', {
            'fields': ('status', 'sent_at', 'error_message')
        }),
        ('Contexte', {
            'fields': ('context_data',)
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('template', 'company', 'created_by')
