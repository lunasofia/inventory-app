"""Tests for the CSV import feature (spec: docs/manual-tests-csv-import.md)."""
import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from catalog.models import Category, Condition, Item
from tests.conftest import category_id
from trips.csv_import import parse_items_csv
from trips.models import PackingItem, Template, TemplateItem, TemplateShare

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _csv_file(content: str, name: str = 'test.csv') -> SimpleUploadedFile:
    """Return an InMemoryUploadedFile from a plain string."""
    return SimpleUploadedFile(name, content.encode('utf-8'), content_type='text/csv')


def _csv_file_bytes(raw: bytes, name: str = 'test.csv') -> SimpleUploadedFile:
    return SimpleUploadedFile(name, raw, content_type='text/csv')


# ---------------------------------------------------------------------------
# Parsing helper — pure unit tests (no DB)
# ---------------------------------------------------------------------------

class TestParseItemsCsv:

    def test_valid_three_column_csv(self):
        content = 'name,quantity,category\nSocks,3,Clothing\nShirt,2,Clothing\n'
        rows, skipped, error = parse_items_csv(io.BytesIO(content.encode()))
        assert error is None
        assert skipped == 0
        assert len(rows) == 2
        assert rows[0] == {'name': 'Socks', 'quantity': 3, 'category_name': 'Clothing'}
        assert rows[1] == {'name': 'Shirt', 'quantity': 2, 'category_name': 'Clothing'}

    def test_header_case_and_order_variation(self):
        content = 'Category,NAME,Quantity\nClothing,Socks,3\n'
        rows, skipped, error = parse_items_csv(io.BytesIO(content.encode()))
        assert error is None
        assert rows[0] == {'name': 'Socks', 'quantity': 3, 'category_name': 'Clothing'}

    def test_leading_bom_tolerated(self):
        # UTF-8 BOM prefix (as Excel exports): prepend the BOM bytes directly
        bom = b'\xef\xbb\xbf'
        content = bom + b'name,quantity,category\nPassport,1,Documents\n'
        rows, skipped, error = parse_items_csv(io.BytesIO(content))
        assert error is None
        assert rows[0]['name'] == 'Passport'

    def test_missing_name_column_returns_error(self):
        content = 'quantity,category\n3,Clothing\n'
        rows, skipped, error = parse_items_csv(io.BytesIO(content.encode()))
        assert error is not None
        assert 'name' in error.lower()
        assert rows == []

    def test_blank_name_row_skipped_and_counted(self):
        content = 'name,quantity\nSocks,1\n  ,2\nShirt,1\n'
        rows, skipped, error = parse_items_csv(io.BytesIO(content.encode()))
        assert error is None
        assert skipped == 1
        assert len(rows) == 2

    def test_quantity_defaults(self):
        content = 'name,quantity\nA,\nB,abc\nC,0\nD,-2\nE,3\n'
        rows, skipped, error = parse_items_csv(io.BytesIO(content.encode()))
        assert error is None
        # A, B, C, D all default to 1; E = 3
        assert rows[0]['quantity'] == 1  # blank
        assert rows[1]['quantity'] == 1  # non-numeric
        assert rows[2]['quantity'] == 1  # 0
        assert rows[3]['quantity'] == 1  # -2
        assert rows[4]['quantity'] == 3  # valid

    def test_category_blank_becomes_none(self):
        content = 'name,quantity,category\nSocks,1,\n'
        rows, skipped, error = parse_items_csv(io.BytesIO(content.encode()))
        assert error is None
        assert rows[0]['category_name'] is None

    def test_category_name_preserved(self):
        content = 'name,quantity,category\nSocks,1,Clothing\n'
        rows, skipped, error = parse_items_csv(io.BytesIO(content.encode()))
        assert error is None
        assert rows[0]['category_name'] == 'Clothing'

    def test_file_size_over_limit_returns_error(self):
        # Build a fake large file object with a size attribute
        big = b'x' * (1024 * 1024 + 1)
        rows, skipped, error = parse_items_csv(io.BytesIO(big))
        assert error is not None
        assert 'large' in error.lower()

    def test_row_count_over_limit_returns_error(self):
        lines = ['name,quantity'] + [f'Item{i},1' for i in range(501)]
        content = '\n'.join(lines)
        rows, skipped, error = parse_items_csv(io.BytesIO(content.encode()))
        assert error is not None
        assert '500' in error

    def test_non_utf8_returns_error(self):
        bad = b'\xff\xfeInvalid encoding'
        rows, skipped, error = parse_items_csv(io.BytesIO(bad))
        assert error is not None
        assert 'utf' in error.lower() or 'decoded' in error.lower() or 'unicode' in error.lower()

    def test_empty_file_returns_error_or_no_rows(self):
        rows, skipped, error = parse_items_csv(io.BytesIO(b''))
        # Either an error is returned or rows is empty — nothing must be created.
        assert rows == [] or error is not None


# ---------------------------------------------------------------------------
# New template from CSV
# ---------------------------------------------------------------------------

class TestTemplateCsvImport:

    def test_creates_template_and_items_success_message(self, auth_client, user):
        csv = _csv_file('name,quantity,category\nSocks,3,Clothing\nShirt,1,\n')
        resp = auth_client.post(reverse('template_import_csv'), {
            'name': 'My CSV Template',
            'file': csv,
        })
        assert resp.status_code == 302
        tpl = Template.objects.get(owner=user, name='My CSV Template')
        items = {ti.name: ti for ti in tpl.items.all()}
        assert set(items) == {'Socks', 'Shirt'}
        assert items['Socks'].quantity == 3
        assert items['Socks'].category.name == 'Clothing'
        assert items['Shirt'].category is None
        # Check success message contains counts
        resp2 = auth_client.get(reverse('template_detail', args=[tpl.pk]))
        assert b'Imported 2' in resp2.content

    def test_duplicate_template_name_rejected_nothing_created(self, auth_client, user):
        Template.objects.create(owner=user, name='Dup')
        csv = _csv_file('name\nSocks\n')
        resp = auth_client.post(reverse('template_import_csv'), {
            'name': 'dup',
            'file': csv,
        })
        assert resp.status_code == 200
        assert b'already have a template' in resp.content
        # Only the originally created one
        assert Template.objects.filter(owner=user).count() == 1

    def test_requires_login(self, client):
        resp = client.get(reverse('template_import_csv'))
        assert resp.status_code == 302
        assert '/login' in resp['Location'] or '/accounts' in resp['Location']

    def test_empty_csv_shows_no_items_found_message(self, auth_client, user):
        # File with header only — no data rows
        csv = _csv_file('name,quantity,category\n')
        resp = auth_client.post(reverse('template_import_csv'), {
            'name': 'Empty Import',
            'file': csv,
        })
        # Should not redirect to template detail — should stay on the form page
        assert resp.status_code == 200
        assert b'No items found' in resp.content
        assert not Template.objects.filter(owner=user, name='Empty Import').exists()

    def test_sort_order_sequential_starting_at_one(self, auth_client, user):
        csv = _csv_file('name\nA\nB\nC\n')
        auth_client.post(reverse('template_import_csv'), {'name': 'Ordered', 'file': csv})
        tpl = Template.objects.get(owner=user, name='Ordered')
        orders = list(tpl.items.order_by('sort_order').values_list('sort_order', flat=True))
        assert orders == [1, 2, 3]


# ---------------------------------------------------------------------------
# Append to existing template
# ---------------------------------------------------------------------------

class TestTemplateItemImport:

    def test_items_appended_after_existing_max_sort_order(self, auth_client, user):
        tpl = Template.objects.create(owner=user, name='Base')
        TemplateItem.objects.create(template=tpl, name='Existing', sort_order=5)
        csv = _csv_file('name\nNew1\nNew2\n')
        resp = auth_client.post(reverse('template_item_import', args=[tpl.pk]), {'file': csv})
        assert resp.status_code == 302
        # Existing item untouched
        assert tpl.items.filter(name='Existing', sort_order=5).exists()
        # New items appended after sort_order 5
        new_orders = sorted(
            tpl.items.exclude(name='Existing').values_list('sort_order', flat=True)
        )
        assert new_orders == [6, 7]

    def test_existing_items_untouched(self, auth_client, user):
        tpl = Template.objects.create(owner=user, name='Base')
        TemplateItem.objects.create(template=tpl, name='Original', quantity=2, sort_order=1)
        csv = _csv_file('name\nNew\n')
        auth_client.post(reverse('template_item_import', args=[tpl.pk]), {'file': csv})
        orig = tpl.items.get(name='Original')
        assert orig.quantity == 2 and orig.sort_order == 1

    def test_viewer_gets_404(self, client, user, other_user):
        tpl = Template.objects.create(owner=user, name='Base')
        TemplateShare.objects.create(template=tpl, shared_with=other_user, permission='view')
        client.force_login(other_user)
        csv = _csv_file('name\nSocks\n')
        resp = client.post(reverse('template_item_import', args=[tpl.pk]), {'file': csv})
        assert resp.status_code == 404

    def test_editor_can_append(self, client, user, other_user):
        tpl = Template.objects.create(owner=user, name='Shared')
        TemplateShare.objects.create(template=tpl, shared_with=other_user, permission='edit')
        client.force_login(other_user)
        csv = _csv_file('name\nSharedItem\n')
        resp = client.post(reverse('template_item_import', args=[tpl.pk]), {'file': csv})
        assert resp.status_code == 302
        assert tpl.items.filter(name='SharedItem').exists()

    def test_categories_resolve_to_acting_user(self, client, user, other_user):
        """An editor importing a CSV gets categories owned by themselves, not the template owner."""
        tpl = Template.objects.create(owner=user, name='Shared')
        TemplateShare.objects.create(template=tpl, shared_with=other_user, permission='edit')
        client.force_login(other_user)
        csv = _csv_file('name,category\nSocks,Clothing\n')
        client.post(reverse('template_item_import', args=[tpl.pk]), {'file': csv})
        item = tpl.items.get(name='Socks')
        assert item.category is not None
        assert item.category.owner == other_user

    def test_non_utf8_file_returns_form_error(self, auth_client, user):
        tpl = Template.objects.create(owner=user, name='Base')
        bad = _csv_file_bytes(b'\xff\xfe bad encoding', 'bad.csv')
        resp = auth_client.post(reverse('template_item_import', args=[tpl.pk]), {'file': bad})
        assert resp.status_code == 200
        assert tpl.items.count() == 0


# ---------------------------------------------------------------------------
# Trip import
# ---------------------------------------------------------------------------

class TestTripItemImport:

    def test_creates_packing_items_with_sequential_sort_order(self, auth_client, user, trip):
        csv = _csv_file('name\nSocks\nShirt\n')
        resp = auth_client.post(reverse('trip_item_import', args=[trip.pk]), {'file': csv})
        assert resp.status_code == 302
        items = list(trip.items.order_by('sort_order'))
        assert len(items) == 2
        assert items[0].sort_order == 1
        assert items[1].sort_order == 2

    def test_catalog_item_created_and_times_used_bumped(self, auth_client, user, trip):
        csv = _csv_file('name\nSunscreen\n')
        auth_client.post(reverse('trip_item_import', args=[trip.pk]), {'file': csv})
        cat_item = Item.objects.get(owner=user, name='Sunscreen')
        assert cat_item.times_used == 1

    def test_default_condition_assigned(self, auth_client, user, trip):
        csv = _csv_file('name\nSocks\n')
        auth_client.post(reverse('trip_item_import', args=[trip.pk]), {'file': csv})
        item = trip.items.get(name='Socks')
        default_cond = Condition.objects.get(owner=user, is_default=True)
        assert item.condition == default_cond

    def test_viewer_gets_404(self, client, user, other_user, trip):
        from trips.models import TripShare
        TripShare.objects.create(trip=trip, shared_with=other_user, permission='view')
        client.force_login(other_user)
        csv = _csv_file('name\nSocks\n')
        resp = client.post(reverse('trip_item_import', args=[trip.pk]), {'file': csv})
        assert resp.status_code == 404

    def test_editor_can_import(self, client, user, other_user, trip):
        from trips.models import TripShare
        TripShare.objects.create(trip=trip, shared_with=other_user, permission='edit')
        client.force_login(other_user)
        csv = _csv_file('name\nSocks\n')
        resp = client.post(reverse('trip_item_import', args=[trip.pk]), {'file': csv})
        assert resp.status_code == 302
        assert trip.items.filter(name='Socks').exists()

    def test_appends_after_existing_items(self, auth_client, user, trip):
        PackingItem.objects.create(trip=trip, name='Existing', sort_order=10)
        csv = _csv_file('name\nNew1\nNew2\n')
        auth_client.post(reverse('trip_item_import', args=[trip.pk]), {'file': csv})
        new_orders = sorted(
            trip.items.exclude(name='Existing').values_list('sort_order', flat=True)
        )
        assert new_orders == [11, 12]


# ---------------------------------------------------------------------------
# Category resolution (case-insensitive, no duplicate)
# ---------------------------------------------------------------------------

class TestCategoryResolution:

    def test_category_reuses_existing_case_insensitive(self, auth_client, user):
        """'clothing' in CSV → reuses existing 'Clothing', no new category created."""
        existing = Category.objects.get(owner=user, name='Clothing')
        cat_count_before = Category.objects.filter(owner=user).count()
        csv = _csv_file('name,category\nSocks,clothing\n')
        auth_client.post(reverse('template_import_csv'), {'name': 'Test', 'file': csv})
        assert Category.objects.filter(owner=user).count() == cat_count_before
        tpl = Template.objects.get(owner=user, name='Test')
        item = tpl.items.get(name='Socks')
        assert item.category == existing

    def test_new_category_name_created(self, auth_client, user):
        """A category name not in the user's list is created."""
        assert not Category.objects.filter(owner=user, name='Camping Gear').exists()
        csv = _csv_file('name,category\nTent,Camping Gear\n')
        auth_client.post(reverse('template_import_csv'), {'name': 'Camp', 'file': csv})
        assert Category.objects.filter(owner=user, name='Camping Gear').exists()


# ---------------------------------------------------------------------------
# Errors and edge cases
# ---------------------------------------------------------------------------

class TestErrorsAndEdgeCases:

    def test_empty_file_no_items_message_nothing_created(self, auth_client, user):
        csv = _csv_file('name,quantity,category\n')
        resp = auth_client.post(reverse('template_import_csv'), {
            'name': 'Empty',
            'file': csv,
        })
        assert resp.status_code == 200
        assert b'No items found' in resp.content
        assert not Template.objects.filter(owner=user, name='Empty').exists()

    def test_non_utf8_file_returns_form_error_nothing_created(self, auth_client, user):
        bad = _csv_file_bytes(b'\xff\xfe bad encoding', 'bad.csv')
        resp = auth_client.post(reverse('template_import_csv'), {
            'name': 'Bad',
            'file': bad,
        })
        assert resp.status_code == 200
        assert not Template.objects.filter(owner=user, name='Bad').exists()

    def test_oversized_file_returns_form_error(self, auth_client, user):
        # Create a file slightly over 1 MB
        header = b'name,quantity,category\n'
        row = b'x' * 100 + b',1,Clothing\n'
        content = header + row * 11000  # ~1.1 MB
        big_csv = _csv_file_bytes(content, 'big.csv')
        resp = auth_client.post(reverse('template_import_csv'), {
            'name': 'Big',
            'file': big_csv,
        })
        assert resp.status_code == 200
        assert not Template.objects.filter(owner=user, name='Big').exists()

    def test_over_row_cap_returns_form_error(self, auth_client, user):
        lines = ['name,quantity'] + [f'Item{i},1' for i in range(501)]
        content = '\n'.join(lines)
        csv = _csv_file(content)
        resp = auth_client.post(reverse('template_import_csv'), {
            'name': 'TooMany',
            'file': csv,
        })
        assert resp.status_code == 200
        assert not Template.objects.filter(owner=user, name='TooMany').exists()

    def test_all_blank_names_zero_valid_rows(self, auth_client, user):
        """All rows have blank names → skipped=N, no template created."""
        csv = _csv_file('name\n  \n\n  \n')
        resp = auth_client.post(reverse('template_import_csv'), {
            'name': 'AllBlank',
            'file': csv,
        })
        assert resp.status_code == 200
        assert b'No items found' in resp.content
        assert not Template.objects.filter(owner=user, name='AllBlank').exists()

    def test_success_message_includes_imported_and_skipped_counts(self, auth_client, user):
        csv = _csv_file('name\nSocks\n  \nShirt\n')  # 2 valid, 1 blank → skipped
        resp = auth_client.post(reverse('template_import_csv'), {
            'name': 'Counts',
            'file': csv,
        })
        assert resp.status_code == 302
        tpl = Template.objects.get(owner=user, name='Counts')
        # Follow redirect to see the flash message
        resp2 = auth_client.get(reverse('template_detail', args=[tpl.pk]))
        assert b'Imported 2' in resp2.content
        assert b'1 row' in resp2.content or b'skipped' in resp2.content
