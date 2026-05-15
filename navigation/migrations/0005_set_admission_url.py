"""Прописывает url_name='admission:root' для NavItem с slug='admission'
после раскатки app `admission`. Сделано отдельной миграцией по тому же
паттерну, что и `0003_set_program_url.py`.
"""
from django.db import migrations


def set_url(apps, schema_editor):
    NavItem = apps.get_model('navigation', 'NavItem')
    NavItem.objects.filter(slug='admission').update(url_name='admission:root')


def unset_url(apps, schema_editor):
    NavItem = apps.get_model('navigation', 'NavItem')
    NavItem.objects.filter(slug='admission').update(url_name='')


class Migration(migrations.Migration):
    dependencies = [
        ('navigation', '0004_set_activities_url'),
        ('admission', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(set_url, unset_url),
    ]
