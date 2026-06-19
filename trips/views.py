from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F, Max
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalog.models import Condition, Item

from .forms import PackingItemForm, TripForm
from .models import PackingItem, Trip


def _get_trip_or_404(user, pk, *, require_edit=False):
    """Fetch a trip the user may access, or 404. Optionally require edit rights."""
    trip = get_object_or_404(Trip, pk=pk)
    permission = trip.permission_for(user)
    if permission is None:
        raise Http404('Trip not found.')
    if require_edit and permission not in ('owner', 'edit'):
        raise Http404('Trip not found.')
    return trip, permission


def _grouped_items(trip):
    """Items grouped by category for display: named categories alphabetically,
    then an 'Uncategorized' group last."""
    groups = {}
    for item in trip.items.select_related('category', 'condition'):
        key = item.category.name if item.category else None
        groups.setdefault(key, []).append(item)
    named = sorted((k for k in groups if k is not None), key=str.lower)
    result = [(name, groups[name]) for name in named]
    if None in groups:
        result.append(('Uncategorized', groups[None]))
    return result


def _remember_item(owner, name, category):
    """Hybrid catalog: find (case-insensitively) or create the user's catalog
    item for this name, bump its usage, and return it."""
    item = Item.objects.filter(owner=owner, name__iexact=name).first()
    if item is None:
        item = Item.objects.create(owner=owner, name=name, category=category)
    Item.objects.filter(pk=item.pk).update(times_used=F('times_used') + 1)
    return item


# --- dashboard & trip CRUD -------------------------------------------------

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
    context = _planning_context(request, trip, permission)
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


# --- packing-list items (planning view) ------------------------------------

def _planning_context(request, trip, permission, add_form=None):
    return {
        'trip': trip,
        'permission': permission,
        'can_edit': permission in ('owner', 'edit'),
        'groups': _grouped_items(trip),
        'add_form': add_form if add_form is not None else PackingItemForm(owner=request.user),
    }


def _render_planning(request, trip, permission, add_form=None, status=200):
    """Render the swappable #planning region (add form + grouped list)."""
    context = _planning_context(request, trip, permission, add_form)
    return render(request, 'trips/_planning.html', context, status=status)


@login_required
@require_POST
def item_add(request, pk):
    trip, permission = _get_trip_or_404(request.user, pk, require_edit=True)
    form = PackingItemForm(request.POST, owner=request.user)
    if form.is_valid():
        item = form.save(commit=False)
        item.trip = trip
        item.catalog_item = _remember_item(request.user, item.name, item.category)
        item.condition = Condition.objects.filter(owner=trip.owner, is_default=True).first()
        item.sort_order = (trip.items.aggregate(m=Max('sort_order'))['m'] or 0) + 1
        item.save()
        return _render_planning(request, trip, permission)
    # Invalid: re-render the region with errors (200 so HTMX performs the swap).
    return _render_planning(request, trip, permission, add_form=form)


@login_required
def item_edit(request, pk, item_pk):
    trip, permission = _get_trip_or_404(request.user, pk, require_edit=True)
    item = get_object_or_404(PackingItem, pk=item_pk, trip=trip)
    if request.method == 'POST':
        form = PackingItemForm(request.POST, instance=item, owner=request.user)
        if form.is_valid():
            updated = form.save(commit=False)
            updated.catalog_item = _remember_item(request.user, updated.name, updated.category)
            updated.save()
            return _render_planning(request, trip, permission)
        return render(request, 'trips/_item_edit_row.html',
                      {'trip': trip, 'item': item, 'form': form})
    form = PackingItemForm(instance=item, owner=request.user)
    return render(request, 'trips/_item_edit_row.html', {'trip': trip, 'item': item, 'form': form})


@login_required
def item_row(request, pk, item_pk):
    """Return a single item's display row (used to cancel an inline edit)."""
    trip, permission = _get_trip_or_404(request.user, pk)
    item = get_object_or_404(PackingItem, pk=item_pk, trip=trip)
    return render(request, 'trips/_item_row.html',
                  {'trip': trip, 'item': item, 'can_edit': permission in ('owner', 'edit')})


@login_required
@require_POST
def item_delete(request, pk, item_pk):
    trip, permission = _get_trip_or_404(request.user, pk, require_edit=True)
    item = get_object_or_404(PackingItem, pk=item_pk, trip=trip)
    item.delete()  # leaves the catalog Item intact — catalog is the user's memory
    return _render_planning(request, trip, permission)


@login_required
def item_suggest(request, pk):
    """Autocomplete: the acting user's catalog items matching the typed name,
    ranked by usage (Item default ordering is -times_used, name)."""
    trip, _ = _get_trip_or_404(request.user, pk, require_edit=True)
    query = request.GET.get('name', '').strip()
    suggestions = []
    if query:
        suggestions = Item.objects.filter(owner=request.user, name__icontains=query)[:8]
    return render(request, 'trips/_item_suggestions.html', {'suggestions': suggestions})
