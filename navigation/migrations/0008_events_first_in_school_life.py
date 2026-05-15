"""Делает «Мероприятия» первым пунктом в секции «Жизнь школы».

Меняем `order` у NavItem(slug='events') на 5 — это меньше, чем у
school-day (10), gallery (30) и остальных пунктов секции, поэтому
events встанет на первое место.
"""
from django.db import migrations


def set_order(apps, schema_editor):
    NavItem = apps.get_model('navigation', 'NavItem')
    NavItem.objects.filter(slug='events').update(order=5)


def reset_order(apps, schema_editor):
    NavItem = apps.get_model('navigation', 'NavItem')
    NavItem.objects.filter(slug='events').update(order=75)


class Migration(migrations.Migration):
    dependencies = [
        ('navigation', '0007_add_events_nav'),
    ]
    operations = [
        migrations.RunPython(set_order, reset_order),
    ]
