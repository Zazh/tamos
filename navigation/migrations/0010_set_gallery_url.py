"""Перенацеливает NavItem(slug='gallery') с заглушки pages:gallery на gallery:list.

Раскатан вместе с выделением gallery в отдельный app. Reverse возвращает
старое значение, чтобы можно было откатить миграцию gallery 0001.
"""
from django.db import migrations


def set_url(apps, schema_editor):
    NavItem = apps.get_model('navigation', 'NavItem')
    NavItem.objects.filter(slug='gallery').update(url_name='gallery:list')


def unset_url(apps, schema_editor):
    NavItem = apps.get_model('navigation', 'NavItem')
    NavItem.objects.filter(slug='gallery').update(url_name='pages:gallery')


class Migration(migrations.Migration):

    dependencies = [
        ('navigation', '0009_navitem_flat_page_alter_navitem_url_name'),
        ('gallery', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(set_url, unset_url),
    ]
