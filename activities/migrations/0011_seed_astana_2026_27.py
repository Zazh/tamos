"""Каталог кружков Астаны на 2026-27 учебный год.

Источник — `data/clubs_2026_27_astana.json` (транскрипт PDF «SPACE COURSE —
центр дополнительного образования», 2026-10-21). Только регион `astana`;
Актау не трогаем.

Логика (идемпотентно):
- кружок ищется в регионе по `name_ru` (текущее имя или старое из `match`);
  найден — обновляется на месте (сохраняем pk и `is_featured`), нет — создаётся;
- группы и слоты кружка пересоздаются с нуля из файла;
- переводы названий/локаций/подписей групп берутся из файла; описания —
  только RU, kk/en обнуляются (старые переводы к новому тексту не относятся),
  добиваются `manage.py translate_activities --region astana`;
- опубликованные кружки Астаны, которых нет в файле, СНИМАЮТСЯ с публикации
  (не удаляются — менеджер может вернуть или удалить в бэкофисе);
  неопубликованные черновики не трогаем.
"""
import json
from datetime import time
from pathlib import Path

from django.db import migrations


REGION_SLUG = 'astana'
LANGS = ('ru', 'kk', 'en')


def _data_path():
    return Path(__file__).resolve().parent.parent / 'data' / 'clubs_2026_27_astana.json'


def _parse_time(s):
    h, m = s.split(':')
    return time(int(h), int(m))


def _set_i18n(obj, base, values):
    """values: dict ru/kk/en или строка (одно значение на все языки)."""
    if isinstance(values, str):
        values = {lang: values for lang in LANGS}
    setattr(obj, base, values.get('ru', '') or '')
    for lang in LANGS:
        setattr(obj, f'{base}_{lang}', values.get(lang, '') or '')


def seed(apps, schema_editor):
    Region = apps.get_model('regions', 'Region')
    Section = apps.get_model('activities', 'ActivitySection')
    Activity = apps.get_model('activities', 'Activity')
    Group = apps.get_model('activities', 'ActivityGroup')
    Slot = apps.get_model('activities', 'ScheduleSlot')

    region = Region.objects.filter(slug=REGION_SLUG).first()
    if region is None:
        return

    with _data_path().open(encoding='utf-8') as f:
        data = json.load(f)

    touched_pks = []
    order = 0
    for section_data in data['sections']:
        section = Section.objects.get(slug=section_data['id'])
        for club in section_data['items']:
            order += 10
            names = [club['name']['ru']] + list(club.get('match', []))
            activity = (
                Activity.objects
                .filter(region=region, name_ru__in=names)
                .order_by('-is_published', 'order', 'pk')
                .first()
            )
            if activity is None:
                activity = Activity(region=region, section=section)

            activity.section = section
            _set_i18n(activity, 'name', club['name'])
            _set_i18n(activity, 'location', club.get('location', ''))
            activity.description = club.get('description', '') or ''
            activity.description_ru = activity.description
            activity.description_kk = ''
            activity.description_en = ''
            activity.is_published = True
            activity.order = order
            activity.save()
            touched_pks.append(activity.pk)

            # Группы и слоты — с нуля.
            activity.groups.all().delete()
            teacher = club.get('teacher') or {}
            for g_order, g in enumerate(club['groups'], start=1):
                group = Group(activity=activity, order=g_order * 10)
                _set_i18n(group, 'label', g.get('label', ''))
                _set_i18n(group, 'teacher_name', teacher.get('name', ''))
                group.teacher_phone = teacher.get('phone', '') or ''
                _set_i18n(group, 'teacher_bio', '')
                group.classes = list(g.get('classes') or range(1, 12))
                group.price = g.get('price', club.get('price'))
                group.students_status = 'recruiting'
                group.min_students = club.get('min_students', 5)
                group.max_students = club.get('max_students', 20)
                group.save()
                for s_order, (day, start, end) in enumerate(g['schedule'], start=1):
                    Slot.objects.create(
                        group=group,
                        day=day,
                        start_time=_parse_time(start),
                        end_time=_parse_time(end),
                        order=s_order * 10,
                    )

    # Всё опубликованное в Астане, чего нет в новом каталоге, — снять с публикации.
    Activity.objects.filter(region=region, is_published=True).exclude(pk__in=touched_pks).update(
        is_published=False, is_featured=False,
    )


def noop(apps, schema_editor):
    """Откат = восстановление из бэкапа БД; обратной трансформации нет."""


class Migration(migrations.Migration):
    dependencies = [
        ('activities', '0010_remove_activity_teacher_bio_and_more'),
        ('regions', '0005_seed_inactive_cities'),
    ]
    operations = [
        migrations.RunPython(seed, noop),
    ]
