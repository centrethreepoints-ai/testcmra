"""
Admin interface for catalog application.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, TaxRate, StockMovement, ProductStock


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'company', 'description']
    list_filter = ['company', 'parent']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent', 'company')


@admin.register(TaxRate)
class TaxRateAdmin(admin.ModelAdmin):
    list_display = ['name', 'rate', 'company', 'is_active']
    list_filter = ['company', 'is_active']
    search_fields = ['name']
    ordering = ['rate', 'name']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'sku', 'product_type', 'category', 'price_ht', 
        'current_stock', 'has_stock', 'is_active', 'company'
    ]
    list_filter = [
        'company', 'product_type', 'category', 'has_stock', 'is_active'
    ]
    search_fields = ['name', 'sku', 'barcode', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('name', 'description', 'category', 'product_type', 'company')
        }),
        ('Prix et TVA', {
            'fields': ('price_ht', 'tax_rate')
        }),
        ('Stock', {
            'fields': ('has_stock', 'current_stock', 'min_stock', 'max_stock')
        }),
        ('Références', {
            'fields': ('sku', 'barcode')
        }),
        ('Statut', {
            'fields': ('is_active',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'tax_rate', 'company')
    
    def stock_status(self, obj):
        if not obj.has_stock:
            return format_html('<span style="color: gray;">N/A</span>')
        elif obj.is_out_of_stock():
            return format_html('<span style="color: red;">Rupture</span>')
        elif obj.is_low_stock():
            return format_html('<span style="color: orange;">Bas</span>')
        else:
            return format_html('<span style="color: green;">Normal</span>')
    
    stock_status.short_description = 'Statut stock'


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'movement_type', 'quantity', 'unit_cost', 
        'stock_before', 'stock_after', 'reference', 'company', 'created_at'
    ]
    list_filter = [
        'company', 'movement_type', 'reference_type', 'created_at'
    ]
    search_fields = ['product__name', 'reference', 'notes']
    ordering = ['-created_at']
    readonly_fields = ['stock_before', 'stock_after', 'created_at']
    
    fieldsets = (
        ('Produit', {
            'fields': ('product', 'company')
        }),
        ('Mouvement', {
            'fields': ('movement_type', 'quantity', 'unit_cost')
        }),
        ('Référence', {
            'fields': ('reference', 'reference_type', 'reference_id')
        }),
        ('Stock', {
            'fields': ('stock_before', 'stock_after'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Métadonnées', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'company', 'created_by')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nouveau mouvement
            obj.created_by = request.user
            obj.stock_before = obj.product.current_stock
        super().save_model(request, obj, form, change)


@admin.register(ProductStock)
class ProductStockAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'current_stock', 'min_stock', 'max_stock', 
        'average_cost', 'last_updated'
    ]
    list_filter = ['product__has_stock']
    search_fields = ['product__name']
    ordering = ['product__name']
    readonly_fields = ['last_updated']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'product__company')
    
    def company(self, obj):
        return obj.product.company
    company.short_description = 'Société'
