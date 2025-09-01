"""
API URLs for billing application.
"""

from django.urls import path
from . import api_views

urlpatterns = [
    # Avoirs (Credit notes) fetchers
    path('credit-notes/<int:pk>/fetch/', api_views.credit_note_fetch, name='api_credit_note_fetch'),
    path('invoices/<int:pk>/for-credit-note/', api_views.invoice_for_credit_note_fetch, name='api_invoice_for_credit_note_fetch'),
]
