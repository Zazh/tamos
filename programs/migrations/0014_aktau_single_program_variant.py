"""В Актау оставить только одну карточку «Программа обучения» — начальную
школу (1–4 класс). Средняя/старшая школа в Актау пока не открыта.

Идемпотентно: ищет все ProgramVariantCard для Aktau с title_ru,
отличным от «Начальная школа», и удаляет их.
"""
from django.db import migrations


KEEP_TITLE_RU = 'Начальная школа'


def forwards(apps, schema_editor):
    ProgramVariantCard = apps.get_model('programs', 'ProgramVariantCard')
    ProgramVariantCard.objects.filter(
        program_page__region__slug='aktau',
    ).exclude(title_ru=KEEP_TITLE_RU).delete()


def noop(apps, schema_editor):
    # Без реверса — миграция чистит контент по решению менеджмента.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('programs', '0013_fix_audience_card_astana'),
    ]
    operations = [
        migrations.RunPython(forwards, noop),
    ]
