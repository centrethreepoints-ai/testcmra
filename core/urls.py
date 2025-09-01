"""
URLs for core application.
"""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Approval Workflows
    path('workflows/', views.workflow_list, name='workflow_list'),
    path('workflows/create/', views.workflow_create, name='workflow_create'),
    path('workflows/<int:pk>/', views.workflow_detail, name='workflow_detail'),
    path('workflows/<int:pk>/edit/', views.workflow_edit, name='workflow_edit'),
    
    # Approval Requests
    path('approvals/', views.approval_request_list, name='approval_request_list'),
    path('approvals/create/', views.create_approval_request, name='create_approval_request'),
    path('approvals/<int:pk>/', views.approval_request_detail, name='approval_request_detail'),
    path('approvals/<int:pk>/action/', views.approval_action, name='approval_action'),
    
    # Dashboard Widgets
    path('widgets/', views.dashboard_widgets, name='dashboard_widgets'),
    
    # Notifications
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/<int:pk>/dismiss/', views.dismiss_notification, name='dismiss_notification'),
]
