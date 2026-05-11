from django.db import migrations


# Города «на будущее»: сидим в БД, но is_active=False, чтобы они не светились
# в публичном переключателе регионов и URL `/<lang>/<slug>/` для них возвращал 404.
# Чтобы запустить регион — поставить is_active=True в админке.
INACTIVE_CITIES = [
    {
        'slug': 'almaty',
        'name_ru': 'Алматы',
        'name_kk': 'Алматы',
        'name_en': 'Almaty',
    },
    {
        'slug': 'shymkent',
        'name_ru': 'Шымкент',
        'name_kk': 'Шымкент',
        'name_en': 'Shymkent',
    },
]


def seed_inactive_cities(apps, schema_editor):
    Region = apps.get_model('regions', 'Region')
    for c in INACTIVE_CITIES:
        Region.objects.update_or_create(
            slug=c['slug'],
            defaults={
                'is_default': False,
                'is_active': False,
                'name': c['name_ru'],
                'name_ru': c['name_ru'],
                'name_kk': c['name_kk'],
                'name_en': c['name_en'],
            },
        )


def unseed_inactive_cities(apps, schema_editor):
    Region = apps.get_model('regions', 'Region')
    Region.objects.filter(slug__in=[c['slug'] for c in INACTIVE_CITIES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('regions', '0004_alter_region_options_remove_region_address_and_more'),
    ]
    operations = [
        migrations.RunPython(seed_inactive_cities, unseed_inactive_cities),
    ]
