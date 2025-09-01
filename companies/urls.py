"""
URLs for companies application.
"""

from django.urls import path
from . import views

app_name = 'companies'

urlpatterns = [
    path('switch/<int:company_id>/', views.switch_company, name='switch_company'),
    path('', views.company_list, name='company_list'),
    path('create/', views.company_create, name='company_create'),
    path('<int:pk>/edit/', views.company_edit, name='company_edit'),
]
