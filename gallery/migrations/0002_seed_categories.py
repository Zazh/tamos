"""Seed категорий-чипов для фотогалереи: общий набор для всех филиалов."""
from django.db import migrations


CATEGORIES = [
    {
        'slug': 'achievements',
        'order': 10,
        'name_ru': 'Достижения',
        'name_kk': 'Жетістіктер',
        'name_en': 'Achievements',
    },
    {
        'slug': 'robotics',
        'order': 20,
        'name_ru': 'Робототехника',
        'name_kk': 'Робототехника',
        'name_en': 'Robotics',
    },
    {
        'slug': 'events',
        'order': 30,
        'name_ru': 'Мероприятие',
        'name_kk': 'Іс-шара',
        'name_en': 'Events',
    },
]


def seed(apps, schema_editor):
    GalleryCategory = apps.get_model('gallery', 'GalleryCategory')
    for c in CATEGORIES:
        GalleryCategory.objects.update_or_create(
            slug=c['slug'],
            defaults={
                'name': c['name_ru'],
                'name_ru': c['name_ru'],
                'name_kk': c['name_kk'],
                'name_en': c['name_en'],
                'order': c['order'],
                'is_published': True,
            },
        )


def unseed(apps, schema_editor):
    GalleryCategory = apps.get_model('gallery', 'GalleryCategory')
    GalleryCategory.objects.filter(slug__in=[c['slug'] for c in CATEGORIES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
