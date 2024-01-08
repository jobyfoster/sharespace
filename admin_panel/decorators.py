from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.contrib import messages


# Custom decorator to check if a user belongs to a specific group.
def group_required(group_name, redirect_url="home"):
    """Requires user membership in a specific group."""

    # Inner function to check if the user is in the specified group.
    def in_group(user, request):
        # Checks if the user is authenticated and either in the specified group or a superuser.
        if user.is_authenticated and (
            user.groups.filter(name=group_name).exists() or user.is_superuser
        ):
            return True
        else:
            # If not, show an error message and return False.
            messages.error(request, "You do not have permission to access this page.")
            return False

    # The actual decorator that wraps the view function.
    def decorator(view_func):
        # Wrapper function for the actual view.
        def _wrapped_view(request, *args, **kwargs):
            # If user is in the group, proceed with the view function.
            if in_group(request.user, request):
                return view_func(request, *args, **kwargs)
            else:
                # Otherwise, redirect to a specified URL (default is "home").
                return redirect(redirect_url)

        return _wrapped_view

    return decorator
