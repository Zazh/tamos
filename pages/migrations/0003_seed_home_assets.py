"""
Перенос hero-фона / видео / 5 картинок галереи из `static/` в `media/`
через FileField/ImageField API. Идемпотентно: пропускает регион, если у
HomePage уже есть hero_image (повторный прогон не дублирует файлы).
"""
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.db import migrations


# Источники в static/ → таргетные имена в media/.
HERO_IMAGE = ('images/hero/building.png', 'building.png')
VIDEO = ('videos/intro.mp4', 'intro.mp4')

GALLERY = [
    ('images/sections-images/library.jpg', 'library.jpg', 'Библиотека', 10),
    ('images/sections-images/school-building.jpg', 'school-building.jpg', 'Здание школы', 20),
    ('images/sections-images/kid.png', 'kid.png', 'Ученик', 30),
    ('images/sections-images/woman.png', 'woman.png', 'Преподаватель', 40),
    ('images/teams/1.jpg', 'team.jpg', 'Команда', 50),
]


def _static_path(rel: str) -> Path:
    return Path(settings.BASE_DIR) / 'static' / rel


def seed_home_assets(apps, schema_editor):
    HomePage = apps.get_model('pages', 'HomePage')
    HomeGalleryImage = apps.get_model('pages', 'HomeGalleryImage')

    for home in HomePage.objects.select_related('region').all():
        if home.hero_image:
            # Уже наполнено — не перезаписываем (идемпотентность для повторных run'ов).
            continue

        with open(_static_path(HERO_IMAGE[0]), 'rb') as f:
            home.hero_image.save(HERO_IMAGE[1], File(f), save=False)
        with open(_static_path(VIDEO[0]), 'rb') as f:
            home.video_file.save(VIDEO[1], File(f), save=False)
        home.save()

        for src, name, alt_ru, order in GALLERY:
            img = HomeGalleryImage(
                home_page=home,
                alt_text=alt_ru,
                alt_text_ru=alt_ru,
                order=order,
            )
            with open(_static_path(src), 'rb') as f:
                img.image.save(name, File(f), save=False)
            img.save()


def unseed_home_assets(apps, schema_editor):
    HomePage = apps.get_model('pages', 'HomePage')
    HomeGalleryImage = apps.get_model('pages', 'HomeGalleryImage')

    # FileField.delete() удаляет файл из media/ помимо строки в БД.
    for img in HomeGalleryImage.objects.all():
        img.image.delete(save=False)
        img.delete()

    for home in HomePage.objects.all():
        if home.hero_image:
            home.hero_image.delete(save=False)
        if home.video_file:
            home.video_file.delete(save=False)
        home.save()


class Migration(migrations.Migration):
    dependencies = [
        ('pages', '0002_seed_home_pages'),
    ]
    operations = [
        migrations.RunPython(seed_home_assets, unseed_home_assets),
    ]
