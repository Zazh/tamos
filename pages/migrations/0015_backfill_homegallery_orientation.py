"""Backfill HomeGalleryImage.orientation for existing rows.

После добавления поля 0014 — у всех существующих картинок default 'square'.
Открываем оригинал через Pillow и проставляем настоящую ориентацию.
Идемпотентно: повторный запуск пересчитает orientation у всех записей.
"""

from django.db import migrations
from PIL import Image, UnidentifiedImageError


def detect(width: int, height: int) -> str:
    if height == 0:
        return 'square'
    ratio = width / height
    if ratio > 1.15:
        return 'wide'
    if ratio < 0.95:
        return 'tall'
    return 'square'


def backfill(apps, schema_editor):
    HomeGalleryImage = apps.get_model('pages', 'HomeGalleryImage')
    for img in HomeGalleryImage.objects.all():
        if not img.image:
            continue
        try:
            with Image.open(img.image) as im:
                w, h = im.size
        except (FileNotFoundError, UnidentifiedImageError, OSError):
            continue
        img.orientation = detect(w, h)
        img.save(update_fields=['orientation'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('pages', '0014_homegalleryimage_orientation'),
    ]
    operations = [
        migrations.RunPython(backfill, noop),
    ]
