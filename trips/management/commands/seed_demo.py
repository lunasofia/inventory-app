"""Seed compelling demo data for a live product demo.

Idempotent: wipes the demo user's trips/templates/catalog, then rebuilds.

    python manage.py seed_demo        # or: make seed-demo

Login: demo@packlist.app / demo12345
"""
from datetime import date

from django.core.management.base import BaseCommand

from accounts.models import User
from catalog.models import Category, Item, seed_user_defaults
from trips.models import (
    Bag, PackingItem, Template, TemplateItem, TemplateReminder, Trip,
    seed_default_reminders,
)

EMAIL = 'demo@packlist.app'
PASSWORD = 'demo12345'


class Command(BaseCommand):
    help = 'Seed (or rebuild) the demo account with realistic sample data.'

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            email=EMAIL, defaults={'display_name': 'Sam'})
        user.display_name = 'Sam'
        user.set_password(PASSWORD)
        user.save()
        if created or not user.categories.exists():
            seed_user_defaults(user)
        if not user.reminders.exists():
            seed_default_reminders(user)

        # Clean slate for repeatable demos
        Trip.objects.filter(owner=user).delete()
        Template.objects.filter(owner=user).delete()
        Item.objects.filter(owner=user).delete()

        Category.objects.get_or_create(owner=user, name='Baby')
        cats = {c.name: c for c in user.categories.all()}
        default_cond = user.conditions.filter(is_default=True).first()

        def cat(name):
            return cats.get(name)

        def catalog(name, category=None, times_used=1):
            item, _ = Item.objects.get_or_create(
                owner=user, name=name, defaults={'category': category})
            item.times_used = times_used
            if category and not item.category:
                item.category = category
            item.save()
            return item

        def add(trip, name, qty=1, category=None, bag=None, packed=False):
            return PackingItem.objects.create(
                trip=trip, name=name, quantity=qty, category=category, bag=bag,
                packed=packed, condition=default_cond,
                catalog_item=catalog(name, category),
                sort_order=trip.items.count(),
            )

        # Pre-seed a richer catalog so autocomplete has good suggestions
        for n, c, u in [
            ('Passport', 'Documents', 6), ('Phone charger', 'Electronics', 9),
            ('Toothbrush', 'Toiletries', 8), ('Wool socks', 'Clothing', 5),
            ('Sunscreen', 'Toiletries', 3), ('Rain jacket', 'Clothing', 4),
            ('Diapers', 'Baby', 4), ('Wipes', 'Baby', 4),
        ]:
            catalog(n, cat(c), u)

        # ---- Trip 1: Iceland Ring Road (PACKING, the hero trip) ----
        iceland = Trip.objects.create(
            owner=user, name='Iceland Ring Road', destination='Reykjavík',
            start_date=date(2026, 7, 4), end_date=date(2026, 7, 14),
            status=Trip.Status.PACKING, notes='Layers! Weather changes fast.')
        carry = Bag.objects.create(trip=iceland, name='Carry-on')
        checked = Bag.objects.create(trip=iceland, name='Checked bag')
        add(iceland, 'Passport', 1, cat('Documents'), carry, packed=True)
        add(iceland, 'Phone charger', 1, cat('Electronics'), carry, packed=True)
        add(iceland, 'Travel adapter', 1, cat('Electronics'), carry, packed=True)
        add(iceland, 'Camera', 1, cat('Electronics'), carry, packed=False)
        add(iceland, 'Motion sickness pills', 1, cat('Health'), carry, packed=False)
        add(iceland, 'Wool sweater', 2, cat('Clothing'), checked, packed=True)
        add(iceland, 'Wool socks', 5, cat('Clothing'), checked, packed=True)
        add(iceland, 'Thermal base layer', 2, cat('Clothing'), checked, packed=True)
        add(iceland, 'Rain jacket', 1, cat('Clothing'), checked, packed=False)
        add(iceland, 'Toothbrush', 1, cat('Toiletries'), checked, packed=False)
        add(iceland, 'Travel shampoo', 1, cat('Toiletries'), checked, packed=False)
        add(iceland, 'Swimsuit (hot springs!)', 1, cat('Clothing'), None, packed=False)

        # ---- Template: Weekend baseline ----
        weekend = Template.objects.create(
            owner=user, name='Weekend baseline',
            description='Our go-to list for a 2-night trip.')
        for n, q, c in [('Toothbrush', 1, 'Toiletries'), ('Phone charger', 1, 'Electronics'),
                        ('T-shirt', 3, 'Clothing'), ('Underwear', 3, 'Clothing'),
                        ('Sunscreen', 1, 'Toiletries')]:
            TemplateItem.objects.create(template=weekend, name=n, quantity=q, category=cat(c))
        for i, text in enumerate(['Check the closet and bathroom', 'Wallet, keys, phone']):
            TemplateReminder.objects.create(template=weekend, text=text, sort_order=i)

        # ---- Trip 2: Family weekend at the lake (PLANNING, from template, modified) ----
        lake = Trip.objects.create(
            owner=user, name='Family weekend at the lake', destination='Lake Tahoe',
            start_date=date(2026, 6, 27), end_date=date(2026, 6, 29),
            status=Trip.Status.PLANNING, origin_template=weekend,
            notes='First trip with the baby — keep it simple.')
        ourbag = Bag.objects.create(trip=lake, name='Our duffel')
        babybag = Bag.objects.create(trip=lake, name='Baby bag')
        add(lake, 'Toothbrush', 1, cat('Toiletries'), ourbag)
        add(lake, 'Phone charger', 1, cat('Electronics'), ourbag)
        add(lake, 'T-shirt', 4, cat('Clothing'), ourbag)          # changed qty vs template
        add(lake, 'Underwear', 3, cat('Clothing'), ourbag)
        add(lake, 'Sunscreen', 1, cat('Toiletries'), ourbag)
        add(lake, 'Diapers', 1, cat('Baby'), babybag)             # added vs template
        add(lake, 'Wipes', 2, cat('Baby'), babybag)               # added vs template
        add(lake, 'Baby monitor', 1, cat('Baby'), babybag)        # added vs template

        # ---- Trip 3: Tokyo (COMPLETE, shows the Completed section) ----
        Trip.objects.create(
            owner=user, name='Tokyo 2024', destination='Tokyo',
            start_date=date(2024, 10, 1), end_date=date(2024, 10, 12),
            status=Trip.Status.COMPLETE)

        self.stdout.write(self.style.SUCCESS(
            f'Demo ready: {EMAIL} / {PASSWORD}'))
        self.stdout.write(
            f'  Trips: {list(Trip.objects.filter(owner=user).values_list("name", "status"))}')
        self.stdout.write(
            f'  Iceland packed: {iceland.packed_count}/{iceland.total_count} '
            f'({iceland.progress_pct}%)')
        self.stdout.write(
            f'  Catalog items: {Item.objects.filter(owner=user).count()}')
