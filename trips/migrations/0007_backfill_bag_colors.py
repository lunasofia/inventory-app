import random
from django.db import migrations

SWATCH_SLUGS = ['amber', 'terracotta', 'sage', 'rose', 'coral', 'sand', 'sky', 'lavender', 'teal', 'lime', 'peach', 'slate']


def backfill_bag_colors(apps, schema_editor):
    Bag = apps.get_model('trips', 'Bag')
    for bag in Bag.objects.all():
        bag.color = random.choice(SWATCH_SLUGS)
        bag.save(update_fields=['color'])


class Migration(migrations.Migration):
    dependencies = [
        ('trips', '0006_bag_color'),
    ]

    operations = [
        migrations.RunPython(backfill_bag_colors, migrations.RunPython.noop),
    ]
