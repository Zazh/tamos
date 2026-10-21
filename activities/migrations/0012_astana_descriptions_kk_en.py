"""Переводы описаний (kk/en) кружков Астаны 2026-27 из `data/clubs_2026_27_astana.json`.

0011 на проде прошла с пустыми kk/en (планировался авто-перевод Gemini, он не
сработал). Переводы добавлены в файл данных руками; эта миграция накатывает их
на уже существующие записи: кружок ищется по `name_ru` в регионе astana,
`description_kk/_en` перезаписываются из файла (RU не трогаем — его мог
подправить менеджер).
"""
import json
from pathlib import Path

from django.db import migrations


def _data_path():
    return Path(__file__).resolve().parent.parent / 'data' / 'clubs_2026_27_astana.json'


def apply_translations(apps, schema_editor):
    Activity = apps.get_model('activities', 'Activity')
    with _data_path().open(encoding='utf-8') as f:
        data = json.load(f)
    for section in data['sections']:
        for club in section['items']:
            desc = club.get('description')
            if not isinstance(desc, dict):
                continue
            Activity.objects.filter(region__slug=data['region'], name_ru=club['name']['ru']).update(
                description_kk=desc.get('kk', '') or '',
                description_en=desc.get('en', '') or '',
            )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('activities', '0011_seed_astana_2026_27'),
    ]
    operations = [
        migrations.RunPython(apply_translations, noop),
    ]
