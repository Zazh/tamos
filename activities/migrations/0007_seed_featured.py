"""Помечает первую активность каждой секции как избранную.

Чтобы лендинг «Программа» не оказался пустым после удаления
`ProgramActivityItem`. Менеджер может в админке поставить/снять
галочку у нужных активностей.

Идемпотентно: если хоть одна активность секции уже избрана —
эта секция пропускается.
"""
from django.db import migrations


def seed_featured(apps, schema_editor):
    Activity = apps.get_model('activities', 'Activity')
    Section = apps.get_model('activities', 'ActivitySection')
    Region = apps.get_model('regions', 'Region')

    for region in Region.objects.filter(is_active=True):
        for section in Section.objects.all():
            qs = Activity.objects.filter(region=region, section=section, is_published=True)
            if qs.filter(is_featured=True).exists():
                continue
            first = qs.order_by('order', 'name').first()
            if first is None:
                continue
            first.is_featured = True
            first.save(update_fields=['is_featured'])


def unset_featured(apps, schema_editor):
    Activity = apps.get_model('activities', 'Activity')
    Activity.objects.update(is_featured=False)


class Migration(migrations.Migration):
    dependencies = [
        ('activities', '0006_activity_is_featured'),
    ]
    operations = [
        migrations.RunPython(seed_featured, unset_featured),
    ]
