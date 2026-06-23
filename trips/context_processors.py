from .models import Trip


def sidebar(request):
    """Make the user's trips available to the persistent sidebar on every page."""
    if not request.user.is_authenticated:
        return {}
    trips = (
        Trip.accessible_by(request.user)
        .select_related('owner')
        .prefetch_related('items')
    )
    return {'sidebar_trips': trips}
