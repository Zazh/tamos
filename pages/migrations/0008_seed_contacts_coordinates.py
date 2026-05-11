from decimal import Decimal

from django.db import migrations


# Координаты — placeholder'ы для seed. Менеджер уточнит точные точки
# офисов через `/admin/pages/contactspage/`.
COORDS = {
    # Astana — район Есиль, центр около пр. Туран 89/1.
    'astana': {
        'latitude': Decimal('51.093900'),
        'longitude': Decimal('71.401100'),
        'map_zoom': 16,
    },
    # Aktau — центр города, точный адрес офиса пока неизвестен.
    'aktau': {
        'latitude': Decimal('43.650000'),
        'longitude': Decimal('51.160000'),
        'map_zoom': 13,
    },
}


def seed_coordinates(apps, schema_editor):
    ContactsPage = apps.get_model('pages', 'ContactsPage')
    for region_slug, fields in COORDS.items():
        ContactsPage.objects.filter(region__slug=region_slug).update(**fields)


def unseed_coordinates(apps, schema_editor):
    ContactsPage = apps.get_model('pages', 'ContactsPage')
    ContactsPage.objects.filter(region__slug__in=list(COORDS)).update(
        latitude=None,
        longitude=None,
        map_zoom=16,
    )


class Migration(migrations.Migration):
    dependencies = [
        ('pages', '0007_remove_contactspage_map_embed_contactspage_latitude_and_more'),
    ]
    operations = [
        migrations.RunPython(seed_coordinates, unseed_coordinates),
    ]
