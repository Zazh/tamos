"""Убирает суффикс «, 1 раз в неделю» из label групп.

В clubs.json у части академических кружков label был в формате
«1-2 классы, 1 раз в неделю» — кратность теперь видна по расписанию
(один слот = один раз в неделю), а длинный текст портит шапку карточки.
"""
import re

from django.db import migrations


SUFFIX_RE = re.compile(r',?\s*1\s+раз\s+в\s+неделю\s*$', re.IGNORECASE)


def strip_suffix(apps, schema_editor):
    Group = apps.get_model('activities', 'ActivityGroup')
    for g in Group.objects.all():
        changed = False
        for field in ('label', 'label_ru', 'label_kk', 'label_en'):
            value = getattr(g, field, None) or ''
            cleaned = SUFFIX_RE.sub('', value).rstrip(' ,')
            if cleaned != value:
                setattr(g, field, cleaned)
                changed = True
        if changed:
            g.save(update_fields=['label', 'label_ru', 'label_kk', 'label_en'])


def noop(apps, schema_editor):
    """Удаление суффикса необратимо — восстановить нечего."""
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('activities', '0007_seed_featured'),
    ]
    operations = [
        migrations.RunPython(strip_suffix, noop),
    ]
