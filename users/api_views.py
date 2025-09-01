"""
API views for users application.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint for users API."""
    return Response({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'service': 'Users API',
        'version': '1.0.0',
    })
