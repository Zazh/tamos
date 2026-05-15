"""Seed справочников: Department (ru/kz) + GradeGroup (1, 2-6, 2-7, 7-11, 8-11).
Идемпотентно (update_or_create по slug).
"""
from django.db import migrations


DEPARTMENTS = [
    {
        'slug': 'ru',
        'order': 10,
        'translations': {
            'ru': 'Русское отделение',
            'kk': 'Орыс бөлімі',
            'en': 'Russian-medium department',
        },
    },
    {
        'slug': 'kz',
        'order': 20,
        'translations': {
            'ru': 'Казахское отделение',
            'kk': 'Қазақ бөлімі',
            'en': 'Kazakh-medium department',
        },
    },
]


GRADE_GROUPS = [
    {
        'slug': '1',
        'order': 10,
        'translations': {
            'ru': ('1 класс', '1 кл.'),
            'kk': ('1 сынып', '1 сын.'),
            'en': ('Grade 1', 'G1'),
        },
    },
    {
        'slug': '2-7',
        'order': 20,
        'translations': {
            'ru': ('2–7 класс', '2–7 кл.'),
            'kk': ('2–7 сынып', '2–7 сын.'),
            'en': ('Grades 2–7', 'G2–7'),
        },
    },
    {
        'slug': '2-6',
        'order': 21,
        'translations': {
            'ru': ('2–6 класс', '2–6 кл.'),
            'kk': ('2–6 сынып', '2–6 сын.'),
            'en': ('Grades 2–6', 'G2–6'),
        },
    },
    {
        'slug': '8-11',
        'order': 30,
        'translations': {
            'ru': ('8–11 класс', '8–11 кл.'),
            'kk': ('8–11 сынып', '8–11 сын.'),
            'en': ('Grades 8–11', 'G8–11'),
        },
    },
    {
        'slug': '7-11',
        'order': 31,
        'translations': {
            'ru': ('7–11 класс', '7–11 кл.'),
            'kk': ('7–11 сынып', '7–11 сын.'),
            'en': ('Grades 7–11', 'G7–11'),
        },
    },
]


def seed_lookups(apps, schema_editor):
    Department = apps.get_model('admission', 'Department')
    GradeGroup = apps.get_model('admission', 'GradeGroup')

    for d in DEPARTMENTS:
        ru = d['translations']['ru']
        obj, _ = Department.objects.update_or_create(
            slug=d['slug'],
            defaults={
                'name': ru,
                'name_ru': ru,
                'name_kk': d['translations']['kk'],
                'name_en': d['translations']['en'],
                'order': d['order'],
            },
        )

    for g in GRADE_GROUPS:
        ru_name, ru_short = g['translations']['ru']
        kk_name, kk_short = g['translations']['kk']
        en_name, en_short = g['translations']['en']
        GradeGroup.objects.update_or_create(
            slug=g['slug'],
            defaults={
                'name': ru_name,
                'name_ru': ru_name,
                'name_kk': kk_name,
                'name_en': en_name,
                'short_name': ru_short,
                'short_name_ru': ru_short,
                'short_name_kk': kk_short,
                'short_name_en': en_short,
                'order': g['order'],
            },
        )


def unseed_lookups(apps, schema_editor):
    # Никогда не удаляем seed-данные на reverse — это может уронить FK
    # из admission_variant. Откатывают через сами модели.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_lookups, unseed_lookups),
    ]
