from django.conf import settings
from django.db import models
from django.db.models import Q


class Trip(models.Model):
    """An event the user packs for (e.g. a trip)."""

    class Status(models.TextChoices):
        PLANNING = 'planning', 'Planning'
        PACKING = 'packing', 'Packing'
        ACTIVE = 'active', 'On the trip'
        UNPACKING = 'unpacking', 'Unpacking'
        COMPLETE = 'complete', 'Complete'

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trips'
    )
    name = models.CharField(max_length=140)
    destination = models.CharField(max_length=140, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.PLANNING
    )
    # The template this trip was created from, if any (for the drift/diff flow).
    origin_template = models.ForeignKey(
        'Template', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='trips_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date', '-created_at']

    def __str__(self):
        return self.name

    @classmethod
    def accessible_by(cls, user):
        """Trips a user owns or has been granted access to via a share."""
        return cls.objects.filter(
            Q(owner=user) | Q(shares__shared_with=user)
        ).distinct()

    def permission_for(self, user):
        """Return 'owner', 'edit', 'view', or None for the given user."""
        if self.owner_id == user.id:
            return 'owner'
        share = self.shares.filter(shared_with=user).first()
        return share.permission if share else None

    def can_edit(self, user):
        return self.permission_for(user) in ('owner', 'edit')

    @property
    def packed_count(self):
        return self.items.filter(packed=True).count()

    @property
    def total_count(self):
        return self.items.count()

    @property
    def progress_pct(self):
        total = self.total_count
        return round(100 * self.packed_count / total) if total else 0


class Bag(models.Model):
    """A per-trip named container (e.g. "Blue duffel"). Items are assigned to a
    bag; deleting a bag leaves its items intact (they become Unbagged)."""

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='bags')
    name = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['trip', 'name'], name='unique_bag_name_per_trip')
        ]

    def __str__(self):
        return self.name

    @property
    def total_count(self):
        return self.items.count()

    @property
    def packed_count(self):
        return self.items.filter(packed=True).count()

    @property
    def is_packed(self):
        """A bag shows as packed when it has items and all of them are packed."""
        total = self.total_count
        return total > 0 and self.packed_count == total


class PackingItem(models.Model):
    """A single line on a trip's packing list."""

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='items')
    bag = models.ForeignKey(
        Bag, on_delete=models.SET_NULL, null=True, blank=True, related_name='items'
    )
    catalog_item = models.ForeignKey(
        'catalog.Item', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='packing_items',
    )
    name = models.CharField(max_length=120)
    category = models.ForeignKey(
        'catalog.Category', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='packing_items',
    )
    quantity = models.PositiveIntegerField(default=1)
    packed = models.BooleanField(default=False)
    returned = models.BooleanField(default=False)
    condition = models.ForeignKey(
        'catalog.Condition', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='packing_items',
    )
    notes = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return f'{self.quantity}× {self.name}'


class TripShare(models.Model):
    """Grants another user view or edit access to a trip."""

    class Permission(models.TextChoices):
        VIEW = 'view', 'Can view'
        EDIT = 'edit', 'Can edit'

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='shares')
    shared_with = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shared_trips'
    )
    permission = models.CharField(
        max_length=4, choices=Permission.choices, default=Permission.VIEW
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['trip', 'shared_with'], name='unique_share_per_user')
        ]

    def __str__(self):
        return f'{self.trip} → {self.shared_with} ({self.permission})'


class Template(models.Model):
    """A reusable packing list saved from (or for) a kind of trip."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='templates'
    )
    name = models.CharField(max_length=140)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['owner', 'name'], name='unique_template_name_per_owner')
        ]

    def __str__(self):
        return self.name


class TemplateItem(models.Model):
    """A line in a template; cloned into PackingItems when used."""

    template = models.ForeignKey(Template, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=120)
    category = models.ForeignKey(
        'catalog.Category', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='template_items',
    )
    quantity = models.PositiveIntegerField(default=1)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name
