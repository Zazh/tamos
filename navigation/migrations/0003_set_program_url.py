"""
Прописывает url_name='programs:detail' для NavItem с slug='program'
после раскатки app `programs`. Сделано отдельной миграцией, чтобы
не править `0002_seed_navigation.py` (тот — initial seed заглушек).
"""
from django.db import migrations


def set_url(apps, schema_editor):
    NavItem = apps.get_model('navigation', 'NavItem')
    NavItem.objects.filter(slug='program').update(url_name='programs:detail')


def unset_url(apps, schema_editor):
    NavItem = apps.get_model('navigation', 'NavItem')
    NavItem.objects.filter(slug='program').update(url_name='')


class Migration(migrations.Migration):
    dependencies = [
        ('navigation', '0002_seed_navigation'),
        ('programs', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(set_url, unset_url),
    ]
