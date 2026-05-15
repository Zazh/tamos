"""Делает Department.name полным («Русское отделение» вместо «Русское»).
В прежнем seed имя было коротким, а в шаблоне breadcrumb приходилось
склеивать `{{ name }} отделение` — это плохо локализовывалось на kk/en
(дублирование «бөлімі»). Теперь полное имя — единый источник правды.

Идемпотентно: повторное применение не меняет уже обновлённые записи."""
from django.db import migrations


NEW_NAMES = {
    'ru': {
        'name_ru': 'Русское отделение',
        'name_kk': 'Орыс бөлімі',
        'name_en': 'Russian-medium department',
    },
    'kz': {
        'name_ru': 'Казахское отделение',
        'name_kk': 'Қазақ бөлімі',
        'name_en': 'Kazakh-medium department',
    },
}


def relabel(apps, schema_editor):
    Department = apps.get_model('admission', 'Department')
    for slug, names in NEW_NAMES.items():
        Department.objects.filter(slug=slug).update(
            name=names['name_ru'],
            **names,
        )


def revert(apps, schema_editor):
    # Откат к коротким именам, чтобы reverse миграции не оставил химер.
    Department = apps.get_model('admission', 'Department')
    Department.objects.filter(slug='ru').update(
        name='Русское', name_ru='Русское', name_kk='Орыс бөлімі',
        name_en='Russian-medium',
    )
    Department.objects.filter(slug='kz').update(
        name='Казахское', name_ru='Казахское', name_kk='Қазақ бөлімі',
        name_en='Kazakh-medium',
    )


class Migration(migrations.Migration):
    dependencies = [
        ('admission', '0003_seed_admission_pages'),
    ]
    operations = [
        migrations.RunPython(relabel, revert),
    ]
