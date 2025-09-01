"""
URLs for reports application.
"""

from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('trial-balance/', views.trial_balance, name='trial_balance'),
    path('general-ledger/', views.general_ledger, name='general_ledger'),
    path('vat-return/', views.vat_return, name='vat_return'),
]
