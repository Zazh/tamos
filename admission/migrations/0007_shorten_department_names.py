"""Убирает слово «отделение» из Department.name: теперь это просто
«Русское» / «Казахское» (kk: «Орыс» / «Қазақ», en: «Russian-medium» /
«Kazakh-medium»). Полная форма в UI больше не нужна — в breadcrumb
и dropdown отделение и так в контексте.

Идемпотентно: повторное применение не меняет уже укороченные записи."""
from django.db import migrations


SHORT_NAMES = {
    'ru': {
        'name_ru': 'Русское',
        'name_kk': 'Орыс',
        'name_en': 'Russian-medium',
    },
    'kz': {
        'name_ru': 'Казахское',
        'name_kk': 'Қазақ',
        'name_en': 'Kazakh-medium',
    },
}


def shorten(apps, schema_editor):
    Department = apps.get_model('admission', 'Department')
    for slug, names in SHORT_NAMES.items():
        Department.objects.filter(slug=slug).update(
            name=names['name_ru'],
            **names,
        )


def revert(apps, schema_editor):
    Department = apps.get_model('admission', 'Department')
    Department.objects.filter(slug='ru').update(
        name='Русское отделение', name_ru='Русское отделение',
        name_kk='Орыс бөлімі', name_en='Russian-medium department',
    )
    Department.objects.filter(slug='kz').update(
        name='Казахское отделение', name_ru='Казахское отделение',
        name_kk='Қазақ бөлімі', name_en='Kazakh-medium department',
    )


class Migration(migrations.Migration):
    dependencies = [
        ('admission', '0006_seed_all_variants'),
    ]
    operations = [
        migrations.RunPython(shorten, revert),
    ]
