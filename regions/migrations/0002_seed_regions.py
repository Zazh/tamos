from django.db import migrations


REGIONS = [
    {
        'slug': 'astana',
        'is_default': True,
        'name_ru': 'Астана',
        'name_kk': 'Астана',
        'name_en': 'Astana',
    },
    {
        'slug': 'aktau',
        'is_default': False,
        'name_ru': 'Актау',
        'name_kk': 'Ақтау',
        'name_en': 'Aktau',
    },
]


def seed_regions(apps, schema_editor):
    Region = apps.get_model('regions', 'Region')
    for r in REGIONS:
        Region.objects.update_or_create(
            slug=r['slug'],
            defaults={
                'is_default': r['is_default'],
                'name': r['name_ru'],
                'name_ru': r['name_ru'],
                'name_kk': r['name_kk'],
                'name_en': r['name_en'],
            },
        )


def unseed_regions(apps, schema_editor):
    Region = apps.get_model('regions', 'Region')
    Region.objects.filter(slug__in=[r['slug'] for r in REGIONS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('regions', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(seed_regions, unseed_regions),
    ]
