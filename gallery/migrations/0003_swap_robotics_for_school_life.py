"""Заменяет категорию `robotics` на `school-life` (Школьная жизнь).

На момент миграции реальных фото в `robotics` ещё нет, поэтому каскадно
менять ссылки не нужно — `GalleryImage.category` это SET_NULL FK.
Reverse возвращает исходные категории один-в-один.
"""
from django.db import migrations


SCHOOL_LIFE = {
    'slug': 'school-life',
    'order': 20,
    'name_ru': 'Школьная жизнь',
    'name_kk': 'Мектеп өмірі',
    'name_en': 'School life',
}

ROBOTICS = {
    'slug': 'robotics',
    'order': 20,
    'name_ru': 'Робототехника',
    'name_kk': 'Робототехника',
    'name_en': 'Robotics',
}


def swap_forward(apps, schema_editor):
    GalleryCategory = apps.get_model('gallery', 'GalleryCategory')
    GalleryCategory.objects.filter(slug=ROBOTICS['slug']).delete()
    GalleryCategory.objects.update_or_create(
        slug=SCHOOL_LIFE['slug'],
        defaults={
            'name': SCHOOL_LIFE['name_ru'],
            'name_ru': SCHOOL_LIFE['name_ru'],
            'name_kk': SCHOOL_LIFE['name_kk'],
            'name_en': SCHOOL_LIFE['name_en'],
            'order': SCHOOL_LIFE['order'],
            'is_published': True,
        },
    )


def swap_backward(apps, schema_editor):
    GalleryCategory = apps.get_model('gallery', 'GalleryCategory')
    GalleryCategory.objects.filter(slug=SCHOOL_LIFE['slug']).delete()
    GalleryCategory.objects.update_or_create(
        slug=ROBOTICS['slug'],
        defaults={
            'name': ROBOTICS['name_ru'],
            'name_ru': ROBOTICS['name_ru'],
            'name_kk': ROBOTICS['name_kk'],
            'name_en': ROBOTICS['name_en'],
            'order': ROBOTICS['order'],
            'is_published': True,
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0002_seed_categories'),
    ]

    operations = [
        migrations.RunPython(swap_forward, swap_backward),
    ]
