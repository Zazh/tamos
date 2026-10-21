"""Правки переводов каталога Астаны 2026-27 после независимого аудита.

Переносит из `data/clubs_2026_27_astana.json` на существующие записи Астаны
(поиск по `name_ru`): name kk/en, location kk/en, description ru/kk/en,
teacher_name kk/en у групп (латиница на EN, казахская орфография на KK).
RU-название не трогаем — по нему ищем.
"""
import json
from pathlib import Path

from django.db import migrations

LANGS = ('ru', 'kk', 'en')


def _data_path():
    return Path(__file__).resolve().parent.parent / 'data' / 'clubs_2026_27_astana.json'


def _as_dict(v):
    return v if isinstance(v, dict) else {lang: (v or '') for lang in LANGS}


def apply_fixes(apps, schema_editor):
    Activity = apps.get_model('activities', 'Activity')
    ActivityGroup = apps.get_model('activities', 'ActivityGroup')
    with _data_path().open(encoding='utf-8') as f:
        data = json.load(f)
    for section in data['sections']:
        for club in section['items']:
            name = _as_dict(club['name'])
            loc = _as_dict(club.get('location', ''))
            desc = _as_dict(club.get('description', ''))
            qs = Activity.objects.filter(region__slug=data['region'], name_ru=name['ru'])
            qs.update(
                name_kk=name.get('kk', ''), name_en=name.get('en', ''),
                location_kk=loc.get('kk', ''), location_en=loc.get('en', ''),
                description=desc.get('ru', ''), description_ru=desc.get('ru', ''),
                description_kk=desc.get('kk', ''), description_en=desc.get('en', ''),
            )
            teacher = _as_dict((club.get('teacher') or {}).get('name', ''))
            ActivityGroup.objects.filter(activity__in=qs, teacher_name_ru=teacher['ru']).update(
                teacher_name_kk=teacher.get('kk', ''), teacher_name_en=teacher.get('en', ''),
            )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('activities', '0012_astana_descriptions_kk_en'),
    ]
    operations = [
        migrations.RunPython(apply_fixes, noop),
    ]
