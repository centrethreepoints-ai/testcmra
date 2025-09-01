"""
URL configuration for CRM Maroc project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API v1
    path('api/v1/', include('core.api_urls')),
    path('api/v1/auth/', include('users.api_urls')),
    path('api/v1/companies/', include('companies.api_urls')),
    path('api/v1/crm/', include('crm.api_urls')),
    path('api/v1/catalog/', include('catalog.api_urls')),
    path('api/v1/billing/', include('billing.api_urls')),
    path('api/v1/accounting/', include('accounting.api_urls')),

    path('api/v1/settings/', include('settingsapp.api_urls')),
    
    # Main application URLs
    path('', include('core.urls')),
    path('users/', include('users.urls')),
    path('companies/', include('companies.urls')),
    path('crm/', include('crm.urls')),
    path('catalog/', include('catalog.urls')),
    path('billing/', include('billing.urls')),
    path('accounting/', include('accounting.urls')),
    path('helpdesk/', include('helpdesk.urls')),

    path('settings/', include('settingsapp.urls')),
    
    # Debug toolbar (only in development)
    path('__debug__/', include('debug_toolbar.urls')),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error handlers
handler404 = 'core.views.handler404'
handler500 = 'core.views.handler500'
