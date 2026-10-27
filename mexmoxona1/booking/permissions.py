from functools import wraps

from django.contrib.auth.models import Group
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

MANAGER_GROUP = 'Menejer'


def ensure_manager_group():
    group, _ = Group.objects.get_or_create(name=MANAGER_GROUP)
    return group


def is_manager(user):
    """Managers use the hotel panel (/panel/) and never need /admin/.

    Admins (is_staff) count as managers too, so they can see everything managers see.
    """
    if not (user.is_authenticated and user.is_active):
        return False
    if not hasattr(user, '_is_manager'):
        user._is_manager = user.is_staff or user.groups.filter(name=MANAGER_GROUP).exists()
    return user._is_manager


def manager_required(view):
    """Anonymous visitors go to the login page; logged-in non-managers get 403."""
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not is_manager(request.user):
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapper
