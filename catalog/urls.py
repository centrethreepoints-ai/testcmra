"""
URLs for catalog application.
"""

from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    # Produits
    path('products/', views.product_list, name='product_list'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('products/create/', views.ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_edit'),
    path('products/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),

    # Catégories
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # Taux de TVA
    path('tax-rates/', views.tax_rate_list, name='tax_rate_list'),
    path('tax-rates/create/', views.tax_rate_create, name='tax_rate_create'),
    path('tax-rates/<int:pk>/edit/', views.tax_rate_edit, name='tax_rate_edit'),
    path('tax-rates/<int:pk>/delete/', views.tax_rate_delete, name='tax_rate_delete'),

    # Gestion des stocks
    path('stock/', views.stock_list, name='stock_list'),
    path('stock/movements/', views.stock_movements, name='stock_movements'),
    path('stock/movements/<int:pk>/', views.stock_movement_detail, name='stock_movement_detail'),
    path('stock/alerts/', views.low_stock_alerts, name='low_stock_alerts'),
    path('stock/adjustment/', views.stock_adjustment, name='stock_adjustment'),
    path('stock/inventory/', views.inventory_list, name='inventory_list'),
    path('stock/inventory/sessions/', views.inventory_session_list, name='inventory_session_list'),
    path('stock/inventory/sessions/create/', views.inventory_session_create, name='inventory_session_create'),
    path('stock/inventory/sessions/<int:pk>/', views.inventory_session_detail, name='inventory_session_detail'),
    path('stock/inventory/sessions/<int:pk>/start/', views.inventory_session_start, name='inventory_session_start'),
    path('stock/inventory/sessions/<int:pk>/close/', views.inventory_session_close, name='inventory_session_close'),
    path('stock/inventory/sessions/<int:pk>/apply/', views.inventory_session_apply, name='inventory_session_apply'),
    path('stock/inventory/export/', views.inventory_export_csv, name='inventory_export_csv'),
    path('stock/inventory/import/', views.inventory_import_csv, name='inventory_import_csv'),

]
