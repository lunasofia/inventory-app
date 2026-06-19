from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from .forms import TripForm
from .models import Trip


def _get_trip_or_404(user, pk, *, require_edit=False):
    """Fetch a trip the user may access, or 404. Optionally require edit rights."""
    trip = get_object_or_404(Trip, pk=pk)
    permission = trip.permission_for(user)
    if permission is None:
        raise Http404('Trip not found.')
    if require_edit and permission not in ('owner', 'edit'):
        raise Http404('Trip not found.')
    return trip, permission


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


@login_required
def trip_create(request):
    if request.method == 'POST':
        form = TripForm(request.POST)
        if form.is_valid():
            trip = form.save(commit=False)
            trip.owner = request.user
            trip.save()
            messages.success(request, f'Created "{trip.name}".')
            return redirect('trip_detail', pk=trip.pk)
    else:
        form = TripForm()
    return render(request, 'trips/trip_form.html', {'form': form, 'mode': 'create'})


@login_required
def trip_detail(request, pk):
    trip, permission = _get_trip_or_404(request.user, pk)
    items = trip.items.select_related('category', 'condition').all()
    context = {
        'trip': trip,
        'permission': permission,
        'can_edit': permission in ('owner', 'edit'),
        'items': items,
    }
    return render(request, 'trips/trip_detail.html', context)


@login_required
def trip_edit(request, pk):
    trip, _ = _get_trip_or_404(request.user, pk, require_edit=True)
    if request.method == 'POST':
        form = TripForm(request.POST, instance=trip)
        if form.is_valid():
            form.save()
            messages.success(request, 'Trip updated.')
            return redirect('trip_detail', pk=trip.pk)
    else:
        form = TripForm(instance=trip)
    return render(request, 'trips/trip_form.html', {'form': form, 'mode': 'edit', 'trip': trip})


@login_required
def trip_delete(request, pk):
    # Only the owner may delete a trip (sharing edit rights don't grant delete).
    trip = get_object_or_404(Trip, pk=pk, owner=request.user)
    if request.method == 'POST':
        name = trip.name
        trip.delete()
        messages.success(request, f'Deleted "{name}".')
        return redirect('dashboard')
    return render(request, 'trips/trip_confirm_delete.html', {'trip': trip})
