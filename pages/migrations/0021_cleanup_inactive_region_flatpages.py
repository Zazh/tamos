"""Удалить mock FlatPage'ы для inactive регионов (almaty/shymkent).

Изначально 0012_seed_flat_pages + 0013_seed_legal_pages заполняли по 9 страниц
на каждый регион в БД (4 региона × 9 = 36 в Astana/Aktau + 18 в almaty/shymkent).
Менеджер просил очистить mock'и для inactive регионов — реальные данные есть
только для активных (astana, aktau).

Идемпотентно: если страниц для inactive-регионов нет — ничего не делаем.
Reverse — no-op (placeholder легко пересоздать через 0012/0013 при необходимости).
"""

from django.db import migrations


def cleanup_inactive(apps, schema_editor):
    FlatPage = apps.get_model('pages', 'FlatPage')
    FlatPage.objects.filter(region__is_active=False).delete()


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0020_rename_brand_tamos_to_space_school'),
        ('regions', '0005_seed_inactive_cities'),
    ]

    operations = [
        migrations.RunPython(cleanup_inactive, noop_reverse),
    ]
