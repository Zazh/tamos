# Заполняет новые поля группы у существующих 4 активностей
# (по `order`: 10=Робототехника, 20=Шахматы, 30=Дебаты, 40=Английский).

from django.db import migrations


# (order, class_range, group_title, schedule, students_text, students_status,
#  location, price, trainer_name, trainer_bio)
ACTIVITY_GROUP_DATA = [
    (10, '1–5 класс', 'Основная группа',
     'Пн, Ср · 14:00–15:30', 'От 5 учеников', 'recruiting',
     'Лаборатория робототехники', '25 000 ₸/мес',
     'Алишеров Тимур Маратович',
     'Инженер-программист, ведёт детские робототехнические соревнования с 2018 года.'),
    (20, '1–11 класс', 'Все уровни',
     'Ср, Пт · 15:00–16:30', 'До 10 учеников', '',
     'Кабинет 204', '15 000 ₸/мес',
     'Кузнецов Дмитрий Олегович',
     'Международный мастер ФИДЕ, рейтинг 2380, ведёт школьников от 1 разряда до КМС.'),
    (30, '8–11 класс', 'Старшая лига',
     'Вт, Чт · 16:00–17:30', 'От 5 учеников', 'recruiting',
     'Кабинет 312', '28 000 ₸/мес',
     'John Smith',
     'Носитель языка, преподаватель IELTS Speaking, готовит к Cambridge English Speaking exam.'),
    (40, '1–7 класс', 'Младшая группа',
     'Пн, Ср, Пт · 13:30–15:00', 'До 10 учеников', 'full',
     'Кабинет 215', '22 000 ₸/мес',
     'Бекова Айгерим Канатовна',
     'Преподаватель английского с международным сертификатом TKT, 7 лет работы с младшими школьниками.'),
]

TRANSLATABLE_FIELDS = (
    'class_range', 'group_title', 'schedule', 'students_text',
    'location', 'price', 'trainer_name', 'trainer_bio',
)


def _with_base(ru_fields: dict) -> dict:
    """Скопировать `*_ru` значения в base-колонки (modeltranslation fallback)."""
    base = {key.removesuffix('_ru'): value
            for key, value in ru_fields.items() if key.endswith('_ru')}
    return {**base, **ru_fields}


def seed_activity_groups(apps, schema_editor):
    ProgramActivityItem = apps.get_model('programs', 'ProgramActivityItem')

    for (order, class_range, group_title, schedule, students_text,
         students_status, location, price, trainer_name, trainer_bio) in ACTIVITY_GROUP_DATA:
        ru = {
            'class_range_ru': class_range,
            'group_title_ru': group_title,
            'schedule_ru': schedule,
            'students_text_ru': students_text,
            'location_ru': location,
            'price_ru': price,
            'trainer_name_ru': trainer_name,
            'trainer_bio_ru': trainer_bio,
        }
        defaults = {
            **_with_base(ru),
            'students_status': students_status,
        }
        # Обновляем все активности с таким `order` (по одной на каждый ProgramPage / регион).
        ProgramActivityItem.objects.filter(order=order).update(**defaults)


def unseed_activity_groups(apps, schema_editor):
    ProgramActivityItem = apps.get_model('programs', 'ProgramActivityItem')
    blank_fields = {f: '' for f in TRANSLATABLE_FIELDS}
    blank_fields.update({f'{f}_{code}': None for f in TRANSLATABLE_FIELDS for code in ('ru', 'kk', 'en')})
    blank_fields['students_status'] = ''
    ProgramActivityItem.objects.filter(order__in=[o[0] for o in ACTIVITY_GROUP_DATA]).update(**blank_fields)


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0008_activity_group_fields'),
    ]

    operations = [
        migrations.RunPython(seed_activity_groups, unseed_activity_groups),
    ]
