"""Backfill video_poster для существующих HomePage с video_file.

Использует ffmpeg subprocess (см. HomePage._generate_video_poster). Если
ffmpeg недоступен — silent skip, миграция не падает (poster останется пустым,
frontend покажет fallback).
"""

from django.db import migrations


def backfill(apps, schema_editor):
    # Берём real модель (не historical), потому что нужен метод _generate_video_poster
    from pages.models import HomePage
    for home in HomePage.objects.exclude(video_file='').exclude(video_file=None):
        if home.video_poster:
            continue
        try:
            home._generate_video_poster()
        except Exception:
            continue


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('pages', '0017_homepage_video_poster'),
    ]
    operations = [
        migrations.RunPython(backfill, noop),
    ]
