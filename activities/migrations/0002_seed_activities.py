"""Seed внеклассных занятий из data/clubs.json для всех активных регионов.

Источник правды — `activities/data/clubs.json`, сгенерированный
`spaceschool/docs/clubs-data/parse_clubs.py`. Заливаем одинаковый набор
в Astana и Aktau как стартовый каталог; менеджер Aktau правит локально.

Идемпотентно: повторный прогон обновляет существующие записи через
update_or_create по логическим ключам (slug секции, name+region для
кружка и тренера, label+activity для группы). Слоты расписания
переcоздаются с нуля при каждом запуске (старые удаляются), чтобы
изменения в clubs.json накатывались чисто.
"""
from datetime import time
from pathlib import Path

from django.db import migrations

import json


SECTION_TITLES = {
    'sports': {
        'ru': 'Спортивные',
        'kk': 'Спорттық',
        'en': 'Sports',
    },
    'creative': {
        'ru': 'Творческие',
        'kk': 'Шығармашылық',
        'en': 'Creative',
    },
    'academic': {
        'ru': 'Академические',
        'kk': 'Академиялық',
        'en': 'Academic',
    },
}

SECTION_ORDER = {'sports': 10, 'creative': 20, 'academic': 30}


def _data_path():
    return Path(__file__).resolve().parent.parent / 'data' / 'clubs.json'


def _format_class_range(groups):
    """Считает «1–11 класс» из всех classes_min/_max групп."""
    nums = []
    for g in groups:
        for c in g.get('classes') or []:
            nums.append(c)
    if not nums:
        return ''
    lo, hi = min(nums), max(nums)
    return f'{lo} класс' if lo == hi else f'{lo}–{hi} класс'


def _classes_bounds(classes):
    if not classes:
        return None, None
    return min(classes), max(classes)


def _parse_time(s):
    h, m = s.split(':')
    return time(int(h), int(m))


def seed(apps, schema_editor):
    Region = apps.get_model('regions', 'Region')
    Section = apps.get_model('activities', 'ActivitySection')
    Activity = apps.get_model('activities', 'Activity')
    Group = apps.get_model('activities', 'ActivityGroup')
    Slot = apps.get_model('activities', 'ScheduleSlot')
    Teacher = apps.get_model('activities', 'Teacher')

    with _data_path().open(encoding='utf-8') as f:
        data = json.load(f)

    # --- Секции (глобальные, без региона) ---
    section_objs = {}
    for s in data['sections']:
        slug = s['id']
        section, _ = Section.objects.update_or_create(
            slug=slug,
            defaults={
                'title': SECTION_TITLES[slug]['ru'],
                'title_ru': SECTION_TITLES[slug]['ru'],
                'title_kk': SECTION_TITLES[slug]['kk'],
                'title_en': SECTION_TITLES[slug]['en'],
                'order': SECTION_ORDER[slug],
            },
        )
        section_objs[slug] = section

    # --- Заливаем кружки в каждый активный регион (Astana + Aktau) ---
    for region in Region.objects.filter(is_active=True):
        global_order = 0
        for section_data in data['sections']:
            section = section_objs[section_data['id']]
            for club in section_data['items']:
                global_order += 10
                # Тренер: справочник per-region. Ключ — (name, phone, region).
                teacher_name = club['teacher']['name']
                phone = club['teacher']['phone']
                phone_raw = club['teacher']['phone_raw']
                teacher, _ = Teacher.objects.update_or_create(
                    region=region,
                    name=teacher_name,
                    phone=phone,
                    defaults={
                        'name_ru': teacher_name,
                        'phone_display': phone_raw,
                    },
                )

                class_range = _format_class_range(club['groups'])
                activity, _ = Activity.objects.update_or_create(
                    region=region,
                    section=section,
                    name=club['name'],
                    defaults={
                        'name_ru': club['name'],
                        'teacher': teacher,
                        'class_range': class_range,
                        'class_range_ru': class_range,
                        'location': club.get('location', ''),
                        'location_ru': club.get('location', ''),
                        'notes': club.get('notes', ''),
                        'is_published': True,
                        'order': global_order,
                    },
                )

                students = club.get('students') or {}
                min_students = students.get('min', 5)
                max_students = students.get('max', 20)

                for g_order, g in enumerate(club['groups'], start=1):
                    label = g.get('label', '') or ''
                    classes = g.get('classes') or []
                    cmin, cmax = _classes_bounds(classes)
                    price = g.get('price')

                    group, _ = Group.objects.update_or_create(
                        activity=activity,
                        label=label,
                        defaults={
                            'label_ru': label,
                            'classes_min': cmin,
                            'classes_max': cmax,
                            'price': price,
                            'students_status': 'recruiting',
                            'min_students': min_students,
                            'max_students': max_students,
                            'order': g_order * 10,
                        },
                    )

                    Slot.objects.filter(group=group).delete()
                    for slot_order, slot in enumerate(g.get('schedule') or [], start=1):
                        Slot.objects.create(
                            group=group,
                            day=slot['day'],
                            start_time=_parse_time(slot['start']),
                            end_time=_parse_time(slot['end']),
                            order=slot_order,
                        )


def unseed(apps, schema_editor):
    # Дропаем всё, что мы насеяли. Section/Teacher без региона уйдут вместе с
    # каскадом по Activity (через FK PROTECT мы это не можем; чистим вручную).
    Activity = apps.get_model('activities', 'Activity')
    Section = apps.get_model('activities', 'ActivitySection')
    Teacher = apps.get_model('activities', 'Teacher')
    Activity.objects.all().delete()
    Teacher.objects.all().delete()
    Section.objects.filter(slug__in=['sports', 'creative', 'academic']).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('activities', '0001_initial'),
        ('regions', '0005_seed_inactive_cities'),
    ]
    operations = [
        migrations.RunPython(seed, unseed),
    ]
