from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.views import redirect_to_login


def role_required(required_role: str):
    """Require the current user to have at least the given role per hierarchy.
    Falls back to dashboard with an error if unauthorized.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            has_perm = getattr(user, 'has_role_permission', None)
            if callable(has_perm) and has_perm(required_role):
                return view_func(request, *args, **kwargs)
            messages.error(request, 'Accès non autorisé.')
            return redirect('core:dashboard')
        return _wrapped
    return decorator


