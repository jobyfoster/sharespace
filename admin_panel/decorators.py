from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.contrib import messages


def group_required(group_name, redirect_url="home"):
    """Requires user membership in a specific group."""

    def in_group(user, request):
        if user.is_authenticated and (
            user.groups.filter(name=group_name).exists() or user.is_superuser
        ):
            return True
        else:
            messages.error(request, "You do not have permission to access this page.")
            return False

    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if in_group(request.user, request):
                return view_func(request, *args, **kwargs)
            else:
                return redirect(redirect_url)

        return _wrapped_view

    return decorator
