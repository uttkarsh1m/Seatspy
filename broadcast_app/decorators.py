from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from functools import wraps

def role_required(role):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden("You must be logged in to access this page.")

            if hasattr(request.user, 'profile') and request.user.profile.user_type == role:
                return view_func(request, *args, **kwargs)

            return HttpResponseForbidden("You are not authorized to access this page.")
        return _wrapped_view
    return decorator
