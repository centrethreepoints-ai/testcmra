"""
URLs for settingsapp application.
"""

from django.urls import path
from . import views

app_name = 'settingsapp'

urlpatterns = [
    path('company/', views.company_settings, name='company_settings'),
]
