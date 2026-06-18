from django.conf import settings
from django.db import models

DEFAULT_CATEGORIES = [
    'Clothing',
    'Toiletries',
    'Electronics',
    'Documents',
    'Health',
    'Misc',
]

# (name, is_default) — is_default marks the "all good" baseline assigned to new
# packing items. Everything else is treated as "needs attention" when unpacking.
DEFAULT_CONDITIONS = [
    ('OK', True),
    ('Missing', False),
    ('Needs restock', False),
    ('Needs laundry', False),
]


class Category(models.Model):
    """A user-owned grouping for items (e.g. Clothing, Toiletries)."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='categories'
    )
    name = models.CharField(max_length=80)

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['owner', 'name'], name='unique_category_per_owner')
        ]

    def __str__(self):
        return self.name


class Condition(models.Model):
    """A user-owned status a packing item can have during/after a trip.

    Seeded with sensible defaults (OK, Missing, Needs restock, Needs laundry)
    but users can add their own (e.g. "Damaged", "Lent out").
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conditions'
    )
    name = models.CharField(max_length=60)
    # The baseline "all good" status assigned to new items. Exactly one per user.
    is_default = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'name']
        constraints = [
            models.UniqueConstraint(fields=['owner', 'name'], name='unique_condition_per_owner')
        ]

    def __str__(self):
        return self.name


class Item(models.Model):
    """A remembered item in a user's personal catalog.

    Populated automatically as users add things to trips; powers autocomplete
    and reuse across future trips (the "hybrid" inventory model).
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='items'
    )
    name = models.CharField(max_length=120)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='items'
    )
    notes = models.TextField(blank=True)
    photo = models.ImageField(upload_to='items/', null=True, blank=True)
    times_used = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-times_used', 'name']
        constraints = [
            models.UniqueConstraint(fields=['owner', 'name'], name='unique_item_per_owner')
        ]

    def __str__(self):
        return self.name


def seed_user_defaults(user):
    """Create the starter categories and conditions for a new user."""
    Category.objects.bulk_create(
        [Category(owner=user, name=name) for name in DEFAULT_CATEGORIES],
        ignore_conflicts=True,
    )
    Condition.objects.bulk_create(
        [
            Condition(owner=user, name=name, is_default=is_default, sort_order=i)
            for i, (name, is_default) in enumerate(DEFAULT_CONDITIONS)
        ],
        ignore_conflicts=True,
    )
