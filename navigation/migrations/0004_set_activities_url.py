"""Прописывает url_name='activities:list' для NavItem с slug='extracurricular'."""
from django.db import migrations


def set_url(apps, schema_editor):
    NavItem = apps.get_model('navigation', 'NavItem')
    NavItem.objects.filter(slug='extracurricular').update(url_name='activities:list')


def unset_url(apps, schema_editor):
    NavItem = apps.get_model('navigation', 'NavItem')
    NavItem.objects.filter(slug='extracurricular').update(url_name='')


class Migration(migrations.Migration):
    dependencies = [
        ('navigation', '0003_set_program_url'),
        ('activities', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(set_url, unset_url),
    ]
