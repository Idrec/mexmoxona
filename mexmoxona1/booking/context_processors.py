from .permissions import is_manager


def manager(request):
    """Makes `is_manager` available in every template."""
    return {'is_manager': is_manager(request.user)}
