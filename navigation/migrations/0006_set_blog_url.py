"""Прописывает url_name='blog:list' для NavItem с slug='blog'."""
from django.db import migrations


def set_url(apps, schema_editor):
    NavItem = apps.get_model('navigation', 'NavItem')
    NavItem.objects.filter(slug='blog').update(url_name='blog:list')


def unset_url(apps, schema_editor):
    NavItem = apps.get_model('navigation', 'NavItem')
    NavItem.objects.filter(slug='blog').update(url_name='')


class Migration(migrations.Migration):
    dependencies = [
        ('navigation', '0005_set_admission_url'),
        ('blog', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(set_url, unset_url),
    ]
