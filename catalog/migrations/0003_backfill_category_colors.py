import random
from django.db import migrations

SWATCH_SLUGS = ['amber', 'terracotta', 'sage', 'rose', 'coral', 'sand', 'sky', 'lavender', 'teal', 'lime', 'peach', 'slate']
DEFAULT_CATEGORY_COLORS = {
    'Clothing': 'amber',
    'Electronics': 'terracotta',
    'Documents': 'sage',
    'Toiletries': 'rose',
    'Health': 'coral',
    'Misc': 'sand',
}


def backfill_category_colors(apps, schema_editor):
    Category = apps.get_model('catalog', 'Category')
    for cat in Category.objects.all():
        cat.color = DEFAULT_CATEGORY_COLORS.get(cat.name) or random.choice(SWATCH_SLUGS)
        cat.save(update_fields=['color'])


class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0002_category_color'),
    ]

    operations = [
        migrations.RunPython(backfill_category_colors, migrations.RunPython.noop),
    ]
