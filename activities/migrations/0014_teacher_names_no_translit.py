"""Имена тренеров НЕ переводим — правило проекта (см. translate_activities):
ФИО копируется ru → kk/en как есть. 0013 ошибочно выставила латиницу на EN и
казахскую орфографию на KK; возвращаем написание из PDF для всех групп Астаны.
"""
from django.db import migrations


def copy_ru_names(apps, schema_editor):
    ActivityGroup = apps.get_model('activities', 'ActivityGroup')
    for g in ActivityGroup.objects.filter(activity__region__slug='astana'):
        ru = (g.teacher_name_ru or g.teacher_name or '').strip()
        if not ru:
            continue
        g.teacher_name = ru
        g.teacher_name_kk = ru
        g.teacher_name_en = ru
        g.save(update_fields=['teacher_name', 'teacher_name_kk', 'teacher_name_en'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('activities', '0013_astana_i18n_fixes'),
    ]
    operations = [
        migrations.RunPython(copy_ru_names, noop),
    ]
