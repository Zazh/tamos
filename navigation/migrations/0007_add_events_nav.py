"""Добавляет NavItem 'events' в секцию 'school-life' и линкует на events:list."""
from django.db import migrations


ITEM = {
    'section_slug': 'school-life',
    'slug': 'events',
    'url_name': 'events:list',
    'order': 75,
    'label_ru': 'Мероприятия',
    'label_kk': 'Іс-шаралар',
    'label_en': 'Events',
}


def add_item(apps, schema_editor):
    NavSection = apps.get_model('navigation', 'NavSection')
    NavItem = apps.get_model('navigation', 'NavItem')
    section = NavSection.objects.filter(slug=ITEM['section_slug']).first()
    if section is None:
        return
    NavItem.objects.update_or_create(
        slug=ITEM['slug'],
        defaults={
            'section': section,
            'label': ITEM['label_ru'],
            'label_ru': ITEM['label_ru'],
            'label_kk': ITEM['label_kk'],
            'label_en': ITEM['label_en'],
            'url_name': ITEM['url_name'],
            'is_top_nav': False,
            'order': ITEM['order'],
            'is_published': True,
        },
    )


def remove_item(apps, schema_editor):
    NavItem = apps.get_model('navigation', 'NavItem')
    NavItem.objects.filter(slug=ITEM['slug']).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('navigation', '0006_set_blog_url'),
        ('events', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(add_item, remove_item),
    ]
