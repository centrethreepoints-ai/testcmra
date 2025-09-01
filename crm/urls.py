"""
URLs for CRM application.
"""

from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    # Parties (clients/fournisseurs)
    path('parties/', views.party_list, name='party_list'),
    path('parties/<int:pk>/', views.party_detail, name='party_detail'),
    path('parties/create/', views.PartyCreateView.as_view(), name='party_create'),
    path('parties/<int:pk>/edit/', views.PartyUpdateView.as_view(), name='party_edit'),
    path('parties/<int:pk>/delete/', views.PartyDeleteView.as_view(), name='party_delete'),
    
    # Contacts
    path('contacts/', views.contact_list, name='contact_list'),
    path('contacts/<int:pk>/', views.contact_detail, name='contact_detail'),
    path('contacts/create/', views.ContactCreateView.as_view(), name='contact_create'),
    path('contacts/<int:pk>/edit/', views.ContactUpdateView.as_view(), name='contact_edit'),
    path('contacts/<int:pk>/delete/', views.ContactDeleteView.as_view(), name='contact_delete'),
]
