"""Рефактор: classes_min/max → ArrayField `classes`; удаление Activity.class_range.

Шаги:
  1. AddField ActivityGroup.classes (ArrayField).
  2. RunPython — переносит существующие данные:
     classes = list(range(classes_min, classes_max + 1))
  3. RemoveField classes_min, classes_max.
  4. RemoveField Activity.class_range + переводы (modeltranslation создаёт
     class_range_ru/_kk/_en); теперь шапка аккордеона считается computed.
"""
from django.contrib.postgres.fields import ArrayField
from django.db import migrations, models


def fill_classes(apps, schema_editor):
    Group = apps.get_model('activities', 'ActivityGroup')
    for g in Group.objects.all():
        if g.classes_min is not None and g.classes_max is not None and g.classes_min <= g.classes_max:
            g.classes = list(range(g.classes_min, g.classes_max + 1))
        else:
            g.classes = []
        g.save(update_fields=['classes'])


def restore_classes(apps, schema_editor):
    Group = apps.get_model('activities', 'ActivityGroup')
    for g in Group.objects.all():
        if g.classes:
            g.classes_min = min(g.classes)
            g.classes_max = max(g.classes)
        else:
            g.classes_min = None
            g.classes_max = None
        g.save(update_fields=['classes_min', 'classes_max'])


class Migration(migrations.Migration):
    dependencies = [
        ('activities', '0002_seed_activities'),
    ]
    operations = [
        migrations.AddField(
            model_name='activitygroup',
            name='classes',
            field=ArrayField(
                models.PositiveSmallIntegerField(),
                blank=True,
                default=list,
                size=11,
                verbose_name='Классы',
                help_text='Список классов, в которых занимаются — напр. [3, 4, 5, 6]. '
                          'Min/max и текст в шапке аккордеона считаются автоматически.',
            ),
        ),
        migrations.RunPython(fill_classes, restore_classes),
        migrations.RemoveField(model_name='activitygroup', name='classes_min'),
        migrations.RemoveField(model_name='activitygroup', name='classes_max'),
        migrations.RemoveField(model_name='activity', name='class_range'),
        migrations.RemoveField(model_name='activity', name='class_range_ru'),
        migrations.RemoveField(model_name='activity', name='class_range_kk'),
        migrations.RemoveField(model_name='activity', name='class_range_en'),
    ]
