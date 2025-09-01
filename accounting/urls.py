"""
URLs for accounting application.
"""

from django.urls import path
from . import views

app_name = 'accounting'

urlpatterns = [
    path('moves/', views.move_list, name='move_list'),
    path('moves/<int:pk>/', views.move_detail, name='move_detail'),
    path('journals/', views.journal_list, name='journal_list'),
    path('accounts/', views.account_list, name='account_list'),

    # Rapports
    path('reports/trial-balance/', views.trial_balance, name='trial_balance'),
    path('reports/general-ledger/', views.general_ledger, name='general_ledger'),
    path('reports/vat-return/', views.vat_return, name='vat_return'),
    path('reports/ar-ap/', views.ar_ap_dashboard, name='ar_ap'),
]
