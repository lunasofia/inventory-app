from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Trip


@login_required
def dashboard(request):
    """Landing page: trips the user owns or has been shared on, by status."""
    trips = (
        Trip.accessible_by(request.user)
        .select_related('owner')
        .prefetch_related('items')
    )
    active_statuses = [
        Trip.Status.PLANNING,
        Trip.Status.PACKING,
        Trip.Status.ACTIVE,
        Trip.Status.UNPACKING,
    ]
    context = {
        'active_trips': [t for t in trips if t.status in active_statuses],
        'complete_trips': [t for t in trips if t.status == Trip.Status.COMPLETE],
    }
    return render(request, 'trips/dashboard.html', context)
