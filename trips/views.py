from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F, Max, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from catalog.models import Category, Condition, Item, SWATCH_SLUGS

from accounts.models import User

from .csv_import import parse_items_csv
from .forms import (
    BagForm,
    CategoryForm,
    ItemsCsvUploadForm,
    PackingItemForm,
    TemplateCsvImportForm,
    TemplateForm,
    TemplateItemForm,
    TemplateShareForm,
    ReminderForm,
    TripForm,
    TripShareForm,
)
from .models import (
    Bag,
    PackingItem,
    Reminder,
    Template,
    TemplateItem,
    TemplateReminder,
    TemplateShare,
    Trip,
    TripReminder,
    TripShare,
)


def _resolve_owner_category(owner, category):
    """Return a Category owned by `owner` matching `category` (by name), creating
    it if needed. Keeps shared-trip categories from leaking across users."""
    if category is None:
        return None
    if category.owner_id == owner.id:
        return category
    cat, _ = Category.objects.get_or_create(owner=owner, name=category.name)
    return cat


def _resolve_category_by_name(owner, name):
    """Find (case-insensitively) or create the owner's category by name.
    Returns None for a blank/None name (used by CSV import)."""
    if not name:
        return None
    cat = Category.objects.filter(owner=owner, name__iexact=name).first()
    if cat is None:
        cat = Category.objects.create(owner=owner, name=name)
    return cat


def _import_summary(n, target_name, skipped):
    """Success message for a CSV import; mentions skipped rows only if any."""
    items = f'{n} item{"" if n == 1 else "s"}'
    tail = f' ({skipped} row{"" if skipped == 1 else "s"} skipped)' if skipped else ''
    return f'Imported {items} into "{target_name}"{tail}.'


def _link_catalog_no_bump(owner, name, category):
    """Find/create the owner's catalog item without incrementing usage."""
    item = Item.objects.filter(owner=owner, name__iexact=name).first()
    if item is None:
        item = Item.objects.create(owner=owner, name=name, category=category)
    return item


def _group_mode(request, trip):
    """Current view lens for a trip ('bag', 'category', or 'all'), kept in
    session during a visit. trip_detail resets it to 'bag' on each full load."""
    mode = request.session.get(f'group_mode_{trip.pk}', 'bag')
    return mode if mode in ('category', 'bag', 'all') else 'bag'


def _get_trip_or_404(user, pk, *, require_edit=False):
    """Fetch a trip the user may access, or 404. Optionally require edit rights."""
    trip = get_object_or_404(Trip, pk=pk)
    permission = trip.permission_for(user)
    if permission is None:
        raise Http404('Trip not found.')
    if require_edit and permission not in ('owner', 'edit'):
        raise Http404('Trip not found.')
    return trip, permission


def _grouped_items(trip, mode='category'):
    """Items grouped for display as a list of (heading, bag_or_none, items).

    Named groups sort alphabetically; the catch-all ('Uncategorized' / 'Unbagged')
    comes last. In 'bag' mode the bag object is included so the template can show
    bag-level controls; in 'category' mode the bag slot is None.
    """
    items = list(trip.items.select_related('category', 'condition', 'bag'))
    if mode == 'all':
        unpacked = [i for i in items if not i.packed]
        packed = [i for i in items if i.packed]
        result = []
        if unpacked:
            result.append((f'To pack — {len(unpacked)}', None, unpacked))
        if packed:
            result.append((f'Packed — {len(packed)}', None, packed))
        return result
    if mode == 'bag':
        bags = {b.id: b for b in trip.bags.all()}
        buckets = {}
        for item in items:
            buckets.setdefault(item.bag_id, []).append(item)
        named = sorted((bid for bid in buckets if bid is not None),
                       key=lambda bid: bags[bid].name.lower())
        result = [(bags[bid].name, bags[bid], buckets[bid]) for bid in named]
        if None in buckets:
            result.append(('Unbagged', None, buckets[None]))
        return result
    # category mode
    buckets = {}
    for item in items:
        buckets.setdefault(item.category.name if item.category else None, []).append(item)
    named = sorted((k for k in buckets if k is not None), key=str.lower)
    result = [(name, None, buckets[name]) for name in named]
    if None in buckets:
        result.append(('Uncategorized', None, buckets[None]))
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
    """Home: jump to the most relevant trip (the trip list lives in the sidebar);
    show a welcome screen when the user has no trips yet."""
    trips = list(Trip.accessible_by(request.user))
    if trips:
        active = [t for t in trips if t.status != Trip.Status.COMPLETE]
        target = active[0] if active else trips[0]
        return redirect('trip_detail', pk=target.pk)
    return render(request, 'trips/dashboard.html', {})


@login_required
def trip_create(request):
    if request.method == 'POST':
        form = TripForm(request.POST, owner=request.user, show_template=True)
        if form.is_valid():
            trip = form.save(commit=False)
            trip.owner = request.user
            selected_templates = list(form.cleaned_data.get('start_from_template') or [])
            if len(selected_templates) == 1:
                trip.origin_template = selected_templates[0]
            trip.save()
            total_added = 0
            for tpl in selected_templates:
                added, _ = _clone_template_into_trip(tpl, trip)
                total_added += added
            if selected_templates:
                n = total_added
                m = len(selected_templates)
                items_word = 'item' if n == 1 else 'items'
                tpls_word = 'template' if m == 1 else 'templates'
                messages.success(request, f'Created "{trip.name}" with {n} {items_word} from {m} {tpls_word}.')
            else:
                messages.success(request, f'Created "{trip.name}".')
            return redirect('trip_detail', pk=trip.pk)
    else:
        form = TripForm(owner=request.user, show_template=True)
    return render(request, 'trips/trip_form.html', {'form': form, 'mode': 'create'})


def _clone_template_into_trip(template, trip, *, skip_existing=True):
    """Copy a template's items into a trip's packing list (catalog-linked, usage not bumped).

    Returns (added_count, skipped_count). When skip_existing is True, items whose
    name (case-insensitive) already exists on the trip are skipped; intra-batch
    duplicates within the same call are also skipped.
    """
    default_cond = Condition.objects.filter(owner=trip.owner, is_default=True).first()
    seen = {n.lower() for n in trip.items.values_list('name', flat=True)}
    next_order = (trip.items.aggregate(m=Max('sort_order'))['m'] or 0) + 1
    added = 0
    skipped = 0
    for ti in template.items.all().order_by('sort_order', 'name'):
        key = ti.name.lower()
        if skip_existing and key in seen:
            skipped += 1
            continue
        category = _resolve_owner_category(trip.owner, ti.category)
        PackingItem.objects.create(
            trip=trip, name=ti.name, category=category, quantity=ti.quantity,
            sort_order=next_order, condition=default_cond,
            catalog_item=_link_catalog_no_bump(trip.owner, ti.name, category),
        )
        seen.add(key)
        next_order += 1
        added += 1
    return added, skipped


@login_required
def trip_detail(request, pk):
    trip, permission = _get_trip_or_404(request.user, pk)
    # Default the view lens to "by bag" on each full page load.
    request.session[f'group_mode_{trip.pk}'] = 'bag'
    context = _planning_context(request, trip, permission)
    context['add_template_options'] = Template.accessible_by(request.user)
    if permission == 'owner':
        context.update(_share_context(request, trip))
    return render(request, 'trips/trip_detail.html', context)


@login_required
@require_POST
def trip_add_template(request, pk):
    trip, permission = _get_trip_or_404(request.user, pk, require_edit=True)
    template_id = request.POST.get('template')
    template = get_object_or_404(Template.accessible_by(request.user), pk=template_id)
    added, skipped = _clone_template_into_trip(template, trip)
    if added == 0 and skipped == 0:
        messages.info(request, f'"{template.name}" has no items to add.')
    elif skipped:
        messages.success(request, f'Added {added} item{"" if added == 1 else "s"} from "{template.name}" ({skipped} skipped as duplicate{"" if skipped == 1 else "s"}).')
    else:
        messages.success(request, f'Added {added} item{"" if added == 1 else "s"} from "{template.name}".')
    return _render_planning(request, trip, permission)


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

def _category_usage(category):
    """How many packing items + template items reference this category."""
    return (
        PackingItem.objects.filter(category=category).count()
        + TemplateItem.objects.filter(category=category).count()
    )


def _categories_panel(request, trip=None, cat_add_form=None, template=None):
    """Context for the reusable category-manager panel. `trip` present => the
    panel lives on the planning view and controls re-render the planning region."""
    cats = [
        {'cat': c, 'usage': _category_usage(c)}
        for c in Category.objects.filter(owner=request.user)
    ]
    if template is not None:
        cat_target = '#template-categories'
    elif trip is not None:
        cat_target = '#planning'
    else:
        cat_target = '#categories'
    return {
        'cats': cats,
        'cat_add_form': cat_add_form if cat_add_form is not None else CategoryForm(owner=request.user),
        'cat_target': cat_target,
        'cat_trip': trip,
        'cat_template': template,
    }


def _planning_context(request, trip, permission, add_form=None, bag_form=None, cat_add_form=None):
    mode = _group_mode(request, trip)
    context = {
        'trip': trip,
        'permission': permission,
        'can_edit': permission in ('owner', 'edit'),
        'group_mode': mode,
        'groups': _grouped_items(trip, mode),
        'bags': trip.bags.all(),
        'unbagged_count': trip.items.filter(bag__isnull=True).count(),
        'add_form': add_form if add_form is not None
        else PackingItemForm(owner=request.user, trip=trip),
        'bag_form': bag_form if bag_form is not None else BagForm(trip=trip),
    }
    context.update(_categories_panel(request, trip, cat_add_form))
    return context


def _render_planning(request, trip, permission, add_form=None, bag_form=None,
                     cat_add_form=None, status=200):
    """Render the swappable #planning region (bags bar + add form + grouped list)."""
    context = _planning_context(request, trip, permission, add_form, bag_form, cat_add_form)
    return render(request, 'trips/_planning.html', context, status=status)


@login_required
def set_group(request, pk):
    """Toggle the grouping lens (category vs bag) for the current visit."""
    trip, permission = _get_trip_or_404(request.user, pk)
    mode = request.GET.get('mode', 'bag')
    request.session[f'group_mode_{trip.pk}'] = mode if mode in ('category', 'bag', 'all') else 'bag'
    return _render_planning(request, trip, permission)


@login_required
@require_POST
def item_add(request, pk):
    trip, permission = _get_trip_or_404(request.user, pk, require_edit=True)
    form = PackingItemForm(request.POST, owner=request.user, trip=trip)
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
        form = PackingItemForm(request.POST, instance=item, owner=request.user, trip=trip)
        if form.is_valid():
            updated = form.save(commit=False)
            updated.catalog_item = _remember_item(request.user, updated.name, updated.category)
            updated.save()
            return _render_planning(request, trip, permission)
        return render(request, 'trips/_item_edit_row.html',
                      {'trip': trip, 'item': item, 'form': form})
    form = PackingItemForm(instance=item, owner=request.user, trip=trip)
    return render(request, 'trips/_item_edit_row.html', {'trip': trip, 'item': item, 'form': form})


# --- bags --------------------------------------------------------------------

@login_required
@require_POST
def bag_create(request, pk):
    trip, permission = _get_trip_or_404(request.user, pk, require_edit=True)
    form = BagForm(request.POST, trip=trip)
    if form.is_valid():
        bag = form.save(commit=False)
        bag.trip = trip
        bag.save()
        return _render_planning(request, trip, permission)
    # Invalid: re-render with the bag form's error.
    return _render_planning(request, trip, permission, bag_form=form)


@login_required
def bag_edit(request, pk, bag_pk):
    """GET returns an inline rename form; POST saves it."""
    trip, permission = _get_trip_or_404(request.user, pk, require_edit=True)
    bag = get_object_or_404(Bag, pk=bag_pk, trip=trip)
    if request.method == 'POST':
        form = BagForm(request.POST, instance=bag, trip=trip)
        if form.is_valid():
            form.save()
            return _render_planning(request, trip, permission)
        return _render_planning(request, trip, permission, bag_form=form)
    form = BagForm(instance=bag, trip=trip)
    return render(request, 'trips/_bag_edit_chip.html', {'trip': trip, 'bag': bag, 'form': form})


@login_required
def bag_chip(request, pk, bag_pk):
    """Return a single bag's display chip (used to cancel an inline rename)."""
    trip, permission = _get_trip_or_404(request.user, pk)
    bag = get_object_or_404(Bag, pk=bag_pk, trip=trip)
    return render(request, 'trips/_bag_chip.html',
                  {'trip': trip, 'bag': bag, 'can_edit': permission in ('owner', 'edit')})


@login_required
@require_POST
def bag_delete(request, pk, bag_pk):
    trip, permission = _get_trip_or_404(request.user, pk, require_edit=True)
    bag = get_object_or_404(Bag, pk=bag_pk, trip=trip)
    bag.delete()  # items survive (FK set null) -> become Unbagged
    return _render_planning(request, trip, permission)


@login_required
@require_POST
def bag_mark(request, pk, bag_pk):
    """Coarse done-stamp: set every item in the bag packed/unpacked at once."""
    trip, permission = _get_trip_or_404(request.user, pk, require_edit=True)
    bag = get_object_or_404(Bag, pk=bag_pk, trip=trip)
    packed = request.POST.get('packed') == 'true'
    bag.items.update(packed=packed)
    return _render_planning(request, trip, permission)


# --- templates / reuse -------------------------------------------------------

def _get_template_or_404(user, pk, *, require_edit=False):
    template = get_object_or_404(Template, pk=pk)
    permission = template.permission_for(user)
    if permission is None:
        raise Http404('Template not found.')
    if require_edit and permission not in ('owner', 'edit'):
        raise Http404('Template not found.')
    return template, permission


@login_required
def save_as_template(request, pk):
    """Save a trip's current list as a new template owned by the acting user."""
    trip, _ = _get_trip_or_404(request.user, pk)  # any access can copy into own template
    if request.method == 'POST':
        form = TemplateForm(request.POST, owner=request.user)
        if form.is_valid():
            template = form.save(commit=False)
            template.owner = request.user
            template.save()
            for pi in trip.items.all().order_by('sort_order', 'name'):
                TemplateItem.objects.create(
                    template=template, name=pi.name,
                    category=_resolve_owner_category(request.user, pi.category),
                    quantity=pi.quantity, sort_order=pi.sort_order,
                )
            messages.success(request, f'Saved template "{template.name}".')
            return redirect('template_detail', pk=template.pk)
    else:
        form = TemplateForm(owner=request.user, initial={'name': trip.name})
    return render(request, 'trips/template_form.html',
                  {'form': form, 'mode': 'save', 'trip': trip})


@login_required
def template_list(request):
    templates = Template.accessible_by(request.user).select_related('owner').prefetch_related('items')
    return render(request, 'trips/template_list.html', {'templates': templates})


def _template_context(request, template, add_form=None, can_edit=None):
    if can_edit is None:
        can_edit = template.can_edit(request.user)
    ctx = {
        'template': template,
        'items': template.items.select_related('category'),
        'add_form': add_form if add_form is not None else TemplateItemForm(owner=request.user),
        'can_edit': can_edit,
    }
    ctx.update(_categories_panel(request, template=template))
    return ctx


@login_required
def template_create(request):
    if request.method == 'POST':
        form = TemplateForm(request.POST, owner=request.user)
        if form.is_valid():
            template = form.save(commit=False)
            template.owner = request.user
            template.save()
            messages.success(request, f'Created template "{template.name}".')
            return redirect('template_detail', pk=template.pk)
    else:
        form = TemplateForm(owner=request.user)
    return render(request, 'trips/template_form.html', {'form': form, 'mode': 'new'})


def _render_template_items(request, template, add_form=None, can_edit=None):
    return render(request, 'trips/_template_items.html',
                  _template_context(request, template, add_form, can_edit))


@login_required
def template_import_csv(request):
    """Create a new template from a CSV upload."""
    if request.method == 'POST':
        form = TemplateCsvImportForm(request.POST, request.FILES, owner=request.user)
        if form.is_valid():
            rows = form.cleaned_data['_parsed_rows']
            skipped = form.cleaned_data['_parsed_skipped']
            if not rows:
                messages.warning(request, 'No items found in the CSV — nothing was created.')
                return render(request, 'trips/template_csv_import.html', {'form': form})
            name = form.cleaned_data['name']
            with transaction.atomic():
                template = Template.objects.create(owner=request.user, name=name)
                for i, row in enumerate(rows, start=1):
                    TemplateItem.objects.create(
                        template=template,
                        name=row['name'],
                        quantity=row['quantity'],
                        category=_resolve_category_by_name(request.user, row['category_name']),
                        sort_order=i,
                    )
            messages.success(request, _import_summary(len(rows), name, skipped))
            return redirect('template_detail', pk=template.pk)
    else:
        form = TemplateCsvImportForm(owner=request.user)
    return render(request, 'trips/template_csv_import.html', {'form': form})


@login_required
def template_item_import(request, pk):
    """Append items from a CSV to an existing template (edit permission required)."""
    template, permission = _get_template_or_404(request.user, pk, require_edit=True)
    if request.method == 'POST':
        form = ItemsCsvUploadForm(request.POST, request.FILES)
        if form.is_valid():
            rows = form.cleaned_data['_parsed_rows']
            skipped = form.cleaned_data['_parsed_skipped']
            if not rows:
                messages.warning(request, 'No items found in the CSV — nothing was added.')
                return redirect('template_detail', pk=template.pk)
            with transaction.atomic():
                base_order = (template.items.aggregate(m=Max('sort_order'))['m'] or 0)
                for i, row in enumerate(rows, start=1):
                    TemplateItem.objects.create(
                        template=template,
                        name=row['name'],
                        quantity=row['quantity'],
                        category=_resolve_category_by_name(request.user, row['category_name']),
                        sort_order=base_order + i,
                    )
            messages.success(request, _import_summary(len(rows), template.name, skipped))
            return redirect('template_detail', pk=template.pk)
    else:
        form = ItemsCsvUploadForm()
    return render(request, 'trips/items_csv_import.html', {
        'form': form,
        'target': template,
        'target_type': 'template',
        'cancel_url': reverse('template_detail', args=[pk]),
    })


@login_required
def trip_item_import(request, pk):
    """Append items from a CSV to a trip's packing list (edit permission required)."""
    trip, permission = _get_trip_or_404(request.user, pk, require_edit=True)
    if request.method == 'POST':
        form = ItemsCsvUploadForm(request.POST, request.FILES)
        if form.is_valid():
            rows = form.cleaned_data['_parsed_rows']
            skipped = form.cleaned_data['_parsed_skipped']
            if not rows:
                messages.warning(request, 'No items found in the CSV — nothing was added.')
                return redirect('trip_detail', pk=trip.pk)
            default_cond = Condition.objects.filter(owner=trip.owner, is_default=True).first()
            with transaction.atomic():
                base_order = (trip.items.aggregate(m=Max('sort_order'))['m'] or 0)
                for i, row in enumerate(rows, start=1):
                    category = _resolve_category_by_name(request.user, row['category_name'])
                    PackingItem.objects.create(
                        trip=trip,
                        name=row['name'],
                        quantity=row['quantity'],
                        category=category,
                        condition=default_cond,
                        catalog_item=_remember_item(request.user, row['name'], category),
                        sort_order=base_order + i,
                    )
            messages.success(request, _import_summary(len(rows), trip.name, skipped))
            return redirect('trip_detail', pk=trip.pk)
    else:
        form = ItemsCsvUploadForm()
    return render(request, 'trips/items_csv_import.html', {
        'form': form,
        'target': trip,
        'target_type': 'trip',
        'cancel_url': reverse('trip_detail', args=[pk]),
    })


@login_required
def template_detail(request, pk):
    template, permission = _get_template_or_404(request.user, pk)
    context = _template_context(request, template)
    context.update(_template_share_context(request, template))
    context.update({'permission': permission, 'reminder_form': ReminderForm()})
    return render(request, 'trips/template_detail.html', context)


@login_required
def template_edit(request, pk):
    template, _ = _get_template_or_404(request.user, pk, require_edit=True)
    if request.method == 'POST':
        form = TemplateForm(request.POST, instance=template, owner=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Template updated.')
            return redirect('template_detail', pk=template.pk)
    else:
        form = TemplateForm(instance=template, owner=request.user)
    return render(request, 'trips/template_form.html',
                  {'form': form, 'mode': 'edit', 'template': template})


@login_required
def template_delete(request, pk):
    template, _ = _get_template_or_404(request.user, pk, require_edit=True)
    if request.method == 'POST':
        name = template.name
        template.delete()
        messages.success(request, f'Deleted template "{name}".')
        return redirect('template_list')
    return render(request, 'trips/template_confirm_delete.html', {'template': template})


@login_required
@require_POST
def template_item_add(request, pk):
    template, permission = _get_template_or_404(request.user, pk, require_edit=True)
    form = TemplateItemForm(request.POST, owner=request.user)
    if form.is_valid():
        item = form.save(commit=False)
        item.template = template
        item.sort_order = (template.items.aggregate(m=Max('sort_order'))['m'] or 0) + 1
        item.save()
        return _render_template_items(request, template, can_edit=template.can_edit(request.user))
    return _render_template_items(request, template, add_form=form, can_edit=template.can_edit(request.user))


@login_required
def template_item_edit(request, pk, item_pk):
    template, _ = _get_template_or_404(request.user, pk, require_edit=True)
    item = get_object_or_404(TemplateItem, pk=item_pk, template=template)
    if request.method == 'POST':
        form = TemplateItemForm(request.POST, instance=item, owner=request.user)
        if form.is_valid():
            form.save()
            return _render_template_items(request, template, can_edit=template.can_edit(request.user))
        return render(request, 'trips/_template_item_edit_row.html',
                      {'template': template, 'item': item, 'form': form})
    form = TemplateItemForm(instance=item, owner=request.user)
    return render(request, 'trips/_template_item_edit_row.html',
                  {'template': template, 'item': item, 'form': form})


@login_required
def template_item_row(request, pk, item_pk):
    template, _ = _get_template_or_404(request.user, pk)
    item = get_object_or_404(TemplateItem, pk=item_pk, template=template)
    return render(request, 'trips/_template_item_row.html', {
        'template': template,
        'item': item,
        'can_edit': template.can_edit(request.user),
    })


@login_required
@require_POST
def template_item_delete(request, pk, item_pk):
    template, _ = _get_template_or_404(request.user, pk, require_edit=True)
    item = get_object_or_404(TemplateItem, pk=item_pk, template=template)
    item.delete()
    return _render_template_items(request, template, can_edit=template.can_edit(request.user))


# --- template sharing -------------------------------------------------------

def _get_template_owner_or_404(user, pk):
    return get_object_or_404(Template, pk=pk, owner=user)


def _recent_collaborators(user):
    return User.objects.filter(
        Q(shared_trips__trip__owner=user) |
        Q(trips__shares__shared_with=user) |
        Q(shared_templates__template__owner=user) |
        Q(templates__shares__shared_with=user)
    ).exclude(pk=user.pk).distinct()


def _template_share_context(request, template, form=None):
    already = template.shares.values_list('shared_with_id', flat=True)
    return {
        'template': template,
        'shares': template.shares.select_related('shared_with'),
        'share_form': form if form is not None else TemplateShareForm(template=template),
        'recent_people': _recent_collaborators(request.user).exclude(pk__in=already)[:8],
        'TemplateShare': TemplateShare,
    }


def _render_template_share_panel(request, template, form=None):
    return render(request, 'trips/_template_share_panel.html', _template_share_context(request, template, form))


@login_required
@require_POST
def template_share_add(request, pk):
    template = _get_template_owner_or_404(request.user, pk)
    form = TemplateShareForm(request.POST, template=template)
    if form.is_valid():
        TemplateShare.objects.update_or_create(
            template=template, shared_with=form.cleaned_data['user'],
            defaults={'permission': form.cleaned_data['permission']},
        )
        return _render_template_share_panel(request, template)
    return _render_template_share_panel(request, template, form=form)


@login_required
@require_POST
def template_share_update(request, pk, share_pk):
    template = _get_template_owner_or_404(request.user, pk)
    share = get_object_or_404(TemplateShare, pk=share_pk, template=template)
    permission = request.POST.get('permission')
    if permission in dict(TemplateShare.Permission.choices):
        share.permission = permission
        share.save(update_fields=['permission'])
    return _render_template_share_panel(request, template)


@login_required
@require_POST
def template_share_revoke(request, pk, share_pk):
    template = _get_template_owner_or_404(request.user, pk)
    get_object_or_404(TemplateShare, pk=share_pk, template=template).delete()
    return _render_template_share_panel(request, template)


@login_required
def template_collaborator_suggest(request, pk):
    template = _get_template_owner_or_404(request.user, pk)
    query = request.GET.get('email', '').strip()
    already = template.shares.values_list('shared_with_id', flat=True)
    people = _recent_collaborators(request.user).exclude(pk__in=already)
    if query:
        people = people.filter(Q(email__icontains=query) | Q(display_name__icontains=query))
    return render(request, 'trips/_collaborator_suggestions.html', {'people': people[:8]})


# --- diff view (drift) -------------------------------------------------------

def _aggregate_items(items):
    """Aggregate a list of (name, quantity, category) rows by case-insensitive
    name, summing quantities. Returns {key: {name, qty, category, category_name}}."""
    agg = {}
    for it in items:
        key = it.name.strip().lower()
        cat_name = it.category.name if it.category else None
        if key not in agg:
            agg[key] = {'name': it.name, 'qty': 0, 'category': it.category, 'category_name': cat_name}
        agg[key]['qty'] += it.quantity
        if agg[key]['category'] is None and it.category is not None:
            agg[key]['category'] = it.category
            agg[key]['category_name'] = cat_name
    return agg


def _template_diff(trip, template):
    trip_map = _aggregate_items(trip.items.select_related('category'))
    tmpl_map = _aggregate_items(template.items.select_related('category'))
    added, removed, changed = [], [], []
    for key, t in trip_map.items():
        if key not in tmpl_map:
            added.append({'key': key, 'name': t['name'], 'qty': t['qty'],
                          'category_name': t['category_name']})
        else:
            m = tmpl_map[key]
            if t['qty'] != m['qty'] or t['category_name'] != m['category_name']:
                changed.append({
                    'key': key, 'name': t['name'],
                    'from_qty': m['qty'], 'to_qty': t['qty'],
                    'from_cat': m['category_name'], 'to_cat': t['category_name'],
                })
    for key, m in tmpl_map.items():
        if key not in trip_map:
            removed.append({'key': key, 'name': m['name'], 'qty': m['qty'],
                            'category_name': m['category_name']})
    return {'added': added, 'removed': removed, 'changed': changed,
            'has_changes': bool(added or removed or changed)}


@login_required
def template_diff(request, pk):
    """Review/promote a trip's changes back into a template (the drift flow)."""
    trip, _ = _get_trip_or_404(request.user, pk)
    tpl_id = request.POST.get('template') or request.GET.get('template')
    if tpl_id:
        template = get_object_or_404(Template, pk=tpl_id, owner=request.user)
    elif trip.origin_template_id and trip.origin_template.owner_id == request.user.id:
        template = trip.origin_template
    else:
        template = None

    if template is None:
        # No usable target: let the user pick one of their templates (or save as new).
        return render(request, 'trips/template_diff.html', {
            'trip': trip, 'template': None,
            'templates': Template.objects.filter(owner=request.user),
        })

    if request.method == 'POST':
        trip_map = _aggregate_items(trip.items.select_related('category'))
        applied = 0
        for sel in request.POST.getlist('apply'):
            typ, _, key = sel.partition(':')
            TemplateItem.objects.filter(template=template, name__iexact=key).delete()
            if typ in ('added', 'changed'):
                t = trip_map.get(key)
                if t:
                    TemplateItem.objects.create(
                        template=template, name=t['name'],
                        category=_resolve_owner_category(request.user, t['category']),
                        quantity=t['qty'],
                    )
            applied += 1
        messages.success(request, f'Applied {applied} change(s) to "{template.name}".')
        return redirect(f"{reverse('template_diff', args=[trip.pk])}?template={template.pk}")

    return render(request, 'trips/template_diff.html', {
        'trip': trip, 'template': template,
        'diff': _template_diff(trip, template),
        'templates': Template.objects.filter(owner=request.user),
    })


# --- category management -----------------------------------------------------

def _opt_trip(request):
    """Optional trip context for category endpoints: present when the panel is
    used on the planning view (controls then re-render the planning region)."""
    tid = request.POST.get('trip') or request.GET.get('trip')
    if not tid:
        return None, None
    return _get_trip_or_404(request.user, tid, require_edit=True)


def _category_chip_ctx(request, category, trip, template=None):
    if template is not None:
        cat_target = '#template-categories'
    elif trip is not None:
        cat_target = '#planning'
    else:
        cat_target = '#categories'
    return {
        'cat': category,
        'usage': _category_usage(category),
        'cat_target': cat_target,
        'cat_trip': trip,
        'cat_template': template,
    }


def _opt_template(request):
    """Optional template context for category endpoints."""
    tid = request.POST.get('template') or request.GET.get('template')
    if not tid:
        return None, None
    return _get_template_or_404(request.user, tid, require_edit=True)


def _render_after_category(request, trip, template=None, cat_add_form=None):
    if trip is not None:
        return _render_planning(request, trip, trip.permission_for(request.user),
                                cat_add_form=cat_add_form)
    if template is not None:
        return render(request, 'trips/_categories.html',
                      _categories_panel(request, None, cat_add_form, template=template))
    return render(request, 'trips/_categories.html',
                  _categories_panel(request, None, cat_add_form))


@login_required
def category_manage(request):
    return render(request, 'trips/category_manage.html', _categories_panel(request, None))


@login_required
@require_POST
def category_add(request):
    trip, _ = _opt_trip(request)
    template, _ = _opt_template(request)
    form = CategoryForm(request.POST, owner=request.user)
    if form.is_valid():
        name = form.cleaned_data['name']
        # Reuse an existing same-name category (case-insensitive) instead of duplicating.
        if not Category.objects.filter(owner=request.user, name__iexact=name).exists():
            Category.objects.create(owner=request.user, name=name)
        return _render_after_category(request, trip, template)
    return _render_after_category(request, trip, template, cat_add_form=form)


@login_required
def category_rename(request, pk):
    trip, _ = _opt_trip(request)
    template, _ = _opt_template(request)
    category = get_object_or_404(Category, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category, owner=request.user)
        if form.is_valid():
            form.save()
            return _render_after_category(request, trip, template)
        ctx = _category_chip_ctx(request, category, trip, template)
        ctx['form'] = form
        return render(request, 'trips/_category_edit_chip.html', ctx)
    ctx = _category_chip_ctx(request, category, trip, template)
    ctx['form'] = CategoryForm(instance=category, owner=request.user)
    return render(request, 'trips/_category_edit_chip.html', ctx)


@login_required
def category_chip(request, pk):
    """Display chip (used to cancel an inline rename)."""
    trip, _ = _opt_trip(request)
    template, _ = _opt_template(request)
    category = get_object_or_404(Category, pk=pk, owner=request.user)
    return render(request, 'trips/_category_chip.html', _category_chip_ctx(request, category, trip, template))


@login_required
@require_POST
def category_delete(request, pk):
    trip, _ = _opt_trip(request)
    template, _ = _opt_template(request)
    category = get_object_or_404(Category, pk=pk, owner=request.user)
    category.delete()  # FKs are SET_NULL -> items everywhere become Uncategorized
    return _render_after_category(request, trip, template)


@login_required
def category_set_color(request, pk):
    """GET: show color picker. POST: save chosen color, return chip."""
    trip, _ = _opt_trip(request)
    template, _ = _opt_template(request)
    category = get_object_or_404(Category, pk=pk, owner=request.user)
    if request.method == 'POST':
        color = request.POST.get('color', '')
        if color in SWATCH_SLUGS:
            category.color = color
            category.save(update_fields=['color'])
        return render(request, 'trips/_category_chip.html',
                      _category_chip_ctx(request, category, trip, template))
    ctx = _category_chip_ctx(request, category, trip, template)
    ctx['swatches'] = SWATCH_SLUGS
    return render(request, 'trips/_category_color_picker.html', ctx)


@login_required
def bag_set_color(request, pk, bag_pk):
    """GET: show color picker. POST: save chosen color, return chip."""
    trip, permission = _get_trip_or_404(request.user, pk, require_edit=True)
    bag = get_object_or_404(Bag, pk=bag_pk, trip=trip)
    if request.method == 'POST':
        color = request.POST.get('color', '')
        if color in SWATCH_SLUGS:
            bag.color = color
            bag.save(update_fields=['color'])
        return render(request, 'trips/_bag_chip.html',
                      {'trip': trip, 'bag': bag, 'can_edit': permission in ('owner', 'edit')})
    return render(request, 'trips/_bag_color_picker.html',
                  {'trip': trip, 'bag': bag, 'swatches': SWATCH_SLUGS,
                   'can_edit': permission in ('owner', 'edit')})


@login_required
def item_row(request, pk, item_pk):
    """Return a single item's display row (used to cancel an inline edit)."""
    trip, permission = _get_trip_or_404(request.user, pk)
    item = get_object_or_404(PackingItem, pk=item_pk, trip=trip)
    return render(request, 'trips/_item_row.html', {
        'trip': trip, 'item': item,
        'can_edit': permission in ('owner', 'edit'),
        'group_mode': _group_mode(request, trip),
    })


@login_required
def item_move(request, pk, item_pk):
    """Quick-reassign an item to another bag (bag lens) or category (category
    lens) without opening the full edit form. The target field follows the
    current group lens."""
    trip, permission = _get_trip_or_404(request.user, pk, require_edit=True)
    item = get_object_or_404(PackingItem, pk=item_pk, trip=trip)
    mode = _group_mode(request, trip)  # 'bag' or 'category' ('all' has no move button)

    if request.method == 'POST':
        target_id = request.POST.get(mode) or None
        if mode == 'bag':
            item.bag = trip.bags.filter(pk=target_id).first() if target_id else None
        else:
            item.category = (Category.objects.filter(owner=request.user, pk=target_id).first()
                             if target_id else None)
        item.save(update_fields=['bag' if mode == 'bag' else 'category'])
        return _render_planning(request, trip, permission)

    targets = (trip.bags.all() if mode == 'bag'
               else Category.objects.filter(owner=request.user))
    return render(request, 'trips/_item_move_row.html', {
        'trip': trip, 'item': item, 'mode': mode, 'targets': targets,
    })


@login_required
@require_POST
def item_delete(request, pk, item_pk):
    trip, permission = _get_trip_or_404(request.user, pk, require_edit=True)
    item = get_object_or_404(PackingItem, pk=item_pk, trip=trip)
    item.delete()  # leaves the catalog Item intact — catalog is the user's memory
    return _render_planning(request, trip, permission)


@login_required
@require_POST
def item_toggle(request, pk, item_pk):
    """Check an item off (or on) directly on the trip board."""
    trip, permission = _get_trip_or_404(request.user, pk, require_edit=True)
    item = get_object_or_404(PackingItem, pk=item_pk, trip=trip)
    item.packed = not item.packed
    item.save(update_fields=['packed'])
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


# --- sharing -----------------------------------------------------------------

def _get_owned_trip_or_404(user, pk):
    return get_object_or_404(Trip, pk=pk, owner=user)


def _recent_collaborators(user):
    """Users this person has collaborated with, either direction: people they've
    shared their trips with, plus owners who've shared trips with them."""
    return User.objects.filter(
        Q(shared_trips__trip__owner=user) | Q(trips__shares__shared_with=user)
    ).exclude(pk=user.pk).distinct()


def _share_context(request, trip, form=None):
    already = trip.shares.values_list('shared_with_id', flat=True)
    return {
        'trip': trip,
        'shares': trip.shares.select_related('shared_with'),
        'share_form': form if form is not None else TripShareForm(trip=trip),
        'recent_people': _recent_collaborators(request.user).exclude(pk__in=already)[:8],
        'TripShare': TripShare,
    }


def _render_share_panel(request, trip, form=None):
    return render(request, 'trips/_share_panel.html', _share_context(request, trip, form))


@login_required
@require_POST
def share_add(request, pk):
    trip = _get_owned_trip_or_404(request.user, pk)
    form = TripShareForm(request.POST, trip=trip)
    if form.is_valid():
        TripShare.objects.update_or_create(
            trip=trip, shared_with=form.cleaned_data['user'],
            defaults={'permission': form.cleaned_data['permission']},
        )
        return _render_share_panel(request, trip)
    return _render_share_panel(request, trip, form=form)


@login_required
@require_POST
def share_update(request, pk, share_pk):
    trip = _get_owned_trip_or_404(request.user, pk)
    share = get_object_or_404(TripShare, pk=share_pk, trip=trip)
    permission = request.POST.get('permission')
    if permission in dict(TripShare.Permission.choices):
        share.permission = permission
        share.save(update_fields=['permission'])
    return _render_share_panel(request, trip)


@login_required
@require_POST
def share_revoke(request, pk, share_pk):
    trip = _get_owned_trip_or_404(request.user, pk)
    get_object_or_404(TripShare, pk=share_pk, trip=trip).delete()
    return _render_share_panel(request, trip)


@login_required
def collaborator_suggest(request, pk):
    """Autocomplete recent collaborators (excluding those already on this trip)."""
    trip = _get_owned_trip_or_404(request.user, pk)
    query = request.GET.get('email', '').strip()
    already = trip.shares.values_list('shared_with_id', flat=True)
    people = _recent_collaborators(request.user).exclude(pk__in=already)
    if query:
        people = people.filter(Q(email__icontains=query) | Q(display_name__icontains=query))
    return render(request, 'trips/_collaborator_suggestions.html', {'people': people[:8]})


# --- reminders & final-check exit page ---------------------------------------

def _seed_trip_reminders(trip):
    """Populate a trip's exit reminders from its template (if any) else the
    owner's default reminders. Runs once (guarded by trip.reminders_seeded)."""
    source = (trip.origin_template.reminders.all() if trip.origin_template_id
              else trip.owner.reminders.all())
    TripReminder.objects.bulk_create(
        [TripReminder(trip=trip, text=r.text, sort_order=r.sort_order) for r in source]
    )
    trip.reminders_seeded = True
    trip.save(update_fields=['reminders_seeded'])


def _exit_context(request, trip, permission):
    unpacked = list(trip.items.filter(packed=False).select_related('category', 'bag'))
    return {
        'trip': trip,
        'permission': permission,
        'can_edit': permission in ('owner', 'edit'),
        'reminders': trip.reminders.all(),
        'unpacked': unpacked,
        'reminder_form': ReminderForm(),
    }


def _render_exit(request, trip, permission):
    return render(request, 'trips/_exit_board.html', _exit_context(request, trip, permission))


@login_required
def exit_page(request, pk):
    trip, permission = _get_trip_or_404(request.user, pk)
    if not trip.reminders_seeded:
        _seed_trip_reminders(trip)
    return render(request, 'trips/exit_page.html', _exit_context(request, trip, permission))


@login_required
@require_POST
def exit_item_toggle(request, pk, item_pk):
    trip, permission = _get_trip_or_404(request.user, pk, require_edit=True)
    item = get_object_or_404(PackingItem, pk=item_pk, trip=trip)
    item.packed = not item.packed
    item.save(update_fields=['packed'])
    return _render_exit(request, trip, permission)


@login_required
@require_POST
def trip_reminder_add(request, pk):
    trip, permission = _get_trip_or_404(request.user, pk, require_edit=True)
    form = ReminderForm(request.POST)
    if form.is_valid():
        order = (trip.reminders.aggregate(m=Max('sort_order'))['m'] or 0) + 1
        TripReminder.objects.create(trip=trip, text=form.cleaned_data['text'], sort_order=order)
    return _render_exit(request, trip, permission)


@login_required
@require_POST
def trip_reminder_toggle(request, pk, reminder_pk):
    trip, permission = _get_trip_or_404(request.user, pk, require_edit=True)
    r = get_object_or_404(TripReminder, pk=reminder_pk, trip=trip)
    r.checked = not r.checked
    r.save(update_fields=['checked'])
    return _render_exit(request, trip, permission)


@login_required
@require_POST
def trip_reminder_delete(request, pk, reminder_pk):
    trip, permission = _get_trip_or_404(request.user, pk, require_edit=True)
    get_object_or_404(TripReminder, pk=reminder_pk, trip=trip).delete()
    return _render_exit(request, trip, permission)


@login_required
@require_POST
def reminders_reset(request, pk):
    """Re-seed this trip's reminders from the owner's defaults / template."""
    trip, permission = _get_trip_or_404(request.user, pk, require_edit=True)
    trip.reminders.all().delete()
    trip.reminders_seeded = False
    trip.save(update_fields=['reminders_seeded'])
    _seed_trip_reminders(trip)
    return _render_exit(request, trip, permission)


# default reminders (user-level, settings)

def _render_default_reminders(request, form=None):
    return render(request, 'trips/_reminders_default.html', {
        'reminders': Reminder.objects.filter(owner=request.user),
        'reminder_form': form if form is not None else ReminderForm(),
    })


@login_required
def reminder_manage(request):
    return render(request, 'trips/reminder_manage.html', {
        'reminders': Reminder.objects.filter(owner=request.user),
        'reminder_form': ReminderForm(),
    })


@login_required
@require_POST
def reminder_add(request):
    form = ReminderForm(request.POST)
    if form.is_valid():
        order = (Reminder.objects.filter(owner=request.user).aggregate(m=Max('sort_order'))['m'] or 0) + 1
        Reminder.objects.create(owner=request.user, text=form.cleaned_data['text'], sort_order=order)
        return _render_default_reminders(request)
    return _render_default_reminders(request, form=form)


@login_required
@require_POST
def reminder_delete(request, pk):
    get_object_or_404(Reminder, pk=pk, owner=request.user).delete()
    return _render_default_reminders(request)


# template reminders

def _render_template_reminders(request, template):
    return render(request, 'trips/_template_reminders.html',
                  {'template': template, 'reminder_form': ReminderForm()})


@login_required
@require_POST
def template_reminder_add(request, pk):
    template, _ = _get_template_or_404(request.user, pk, require_edit=True)
    form = ReminderForm(request.POST)
    if form.is_valid():
        order = (template.reminders.aggregate(m=Max('sort_order'))['m'] or 0) + 1
        TemplateReminder.objects.create(template=template, text=form.cleaned_data['text'], sort_order=order)
    return _render_template_reminders(request, template)


@login_required
@require_POST
def template_reminder_delete(request, pk, reminder_pk):
    template, _ = _get_template_or_404(request.user, pk, require_edit=True)
    get_object_or_404(TemplateReminder, pk=reminder_pk, template=template).delete()
    return _render_template_reminders(request, template)
