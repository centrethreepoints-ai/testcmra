"""
API views for core application.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """API endpoint pour vérification de santé."""
    return Response({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'service': 'CRM Maroc API',
        'version': '1.0.0',
    })
