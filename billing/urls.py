"""
URLs for billing application.
"""

from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    # Devis
    path('quotes/', views.quote_list, name='quote_list'),
    path('quotes/create/', views.quote_create, name='quote_create'),
    path('quotes/<int:pk>/', views.quote_detail, name='quote_detail'),
    path('quotes/<int:pk>/edit/', views.quote_edit, name='quote_edit'),
    path('quotes/<int:pk>/delete/', views.quote_delete, name='quote_delete'),
    path('quotes/<int:pk>/to-po/', views.quote_to_po, name='quote_to_po'),
    path('quotes/<int:pk>/mark-sent/', views.quote_mark_sent, name='quote_mark_sent'),
    path('quotes/<int:pk>/pdf/', views.quote_pdf, name='quote_pdf'),
    path('quotes/add-line/', views.quote_add_line, name='quote_add_line'),

    # Factures
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/create/', views.invoice_create, name='invoice_create'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:pk>/edit/', views.invoice_edit, name='invoice_edit'),
    path('invoices/<int:pk>/delete/', views.invoice_delete, name='invoice_delete'),
    path('invoices/<int:pk>/quick-pay/', views.invoice_quick_pay, name='invoice_quick_pay'),
    path('invoices/<int:pk>/mark-validated/', views.invoice_mark_validated, name='invoice_mark_validated'),
    path('invoices/<int:pk>/mark-sent/', views.invoice_mark_sent, name='invoice_mark_sent'),
    path('invoices/<int:pk>/pdf/', views.invoice_pdf, name='invoice_pdf'),

    # Bons de commande
    path('purchase-orders/', views.purchase_order_list, name='purchase_order_list'),
    path('purchase-orders/create/', views.purchase_order_create, name='purchase_order_create'),
    path('purchase-orders/<int:pk>/', views.purchase_order_detail, name='purchase_order_detail'),
    path('purchase-orders/<int:pk>/confirm/', views.purchase_order_confirm, name='purchase_order_confirm'),
    path('purchase-orders/<int:pk>/receive/', views.purchase_order_receive, name='purchase_order_receive'),
    path('purchase-orders/<int:pk>/to-invoice/', views.po_to_invoice, name='po_to_invoice'),
    path('purchase-orders/<int:pk>/mark-sent/', views.purchase_order_mark_sent, name='purchase_order_mark_sent'),
    path('purchase-orders/<int:pk>/pdf/', views.purchase_order_pdf, name='purchase_order_pdf'),

    # Paiements
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/create/', views.payment_create, name='payment_create'),

    # Avoirs
    path('credit-notes/', views.credit_note_list, name='credit_note_list'),
    path('credit-notes/create/', views.credit_note_create, name='credit_note_create'),
    path('credit-notes/<int:pk>/', views.credit_note_detail, name='credit_note_detail'),
    path('credit-notes/<int:pk>/pdf/', views.credit_note_pdf, name='credit_note_pdf'),

    # Fragments / HTMX
    path('product-price/', views.product_price, name='product_price'),
]
