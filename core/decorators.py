# core/decorators.py
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def role_required(role):
    """Decorator to check if a user has a specific role."""
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return user_passes_test(lambda u: False)(view_func)(request, *args, **kwargs)
            if request.user.role != role:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

admin_required = role_required('ADMIN')
lecturer_required = role_required('LECTURER')
student_required = role_required('STUDENT')
