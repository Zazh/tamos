"""Seed FlatPage заглушек для каждого региона и привязка к NavItem.

Контент-плейсхолдеры: editor наполняет реальный текст через админку.
Перечень покрывает все «школьная жизнь» пустые пункты + «О нас».

Идемпотентно: update_or_create по (region, slug).
"""
from django.db import migrations


PLACEHOLDER_CONTENT = {
    'ru': (
        '<p>Этот раздел готовится — мы скоро его наполним. '
        'Если у вас есть вопрос, напишите нам через страницу '
        '«Контакты», мы ответим.</p>'
    ),
    'kk': (
        '<p>Бұл бөлім дайындалуда — жуырда толтырамыз. '
        'Сұрағыңыз болса, «Байланыс» бетінен жазыңыз.</p>'
    ),
    'en': (
        '<p>This page is being prepared. If you have a question, '
        'reach out via the Contacts page.</p>'
    ),
}


# (flat_slug, nav_item_slug, ru_title, kk_title, en_title)
# nav_item_slug — по которому ищем NavItem для привязки flat_page FK.
PAGES = [
    ('about', 'about', 'О нас', 'Біз туралы', 'About us'),
    ('school-day', 'school-day', 'Один день в школе', 'Мектептегі бір күн', 'A day at school'),
    ('safety', 'safety', 'Безопасность', 'Қауіпсіздік', 'Safety'),
    ('uniform', 'uniform', 'Школьная форма', 'Мектеп формасы', 'Uniform'),
    ('supplies', 'supplies', 'Школьные принадлежности', 'Мектеп құралдары', 'Supplies'),
    ('food', 'food', 'Питание', 'Тамақтану', 'Meals'),
    ('transport', 'transport', 'Операторы развозки', 'Тасымалдау', 'Transport'),
]


def seed(apps, schema_editor):
    Region = apps.get_model('regions', 'Region')
    FlatPage = apps.get_model('pages', 'FlatPage')
    NavItem = apps.get_model('navigation', 'NavItem')

    regions = list(Region.objects.all())
    if not regions:
        return

    for region in regions:
        for slug, _nav_slug, ru, kk, en in PAGES:
            FlatPage.objects.update_or_create(
                region=region,
                slug=slug,
                defaults={
                    'title': ru,
                    'title_ru': ru,
                    'title_kk': kk,
                    'title_en': en,
                    'content': PLACEHOLDER_CONTENT['ru'],
                    'content_ru': PLACEHOLDER_CONTENT['ru'],
                    'content_kk': PLACEHOLDER_CONTENT['kk'],
                    'content_en': PLACEHOLDER_CONTENT['en'],
                    'is_published': True,
                },
            )

    # Привязка NavItem.flat_page. NavItem общий для всех регионов, поэтому
    # привязываем к FlatPage любого региона (резолв URL добавляет
    # region_slug из request — см. nav_tags.nav_url). Берём первый регион
    # по порядку — slug в FlatPage везде одинаковый.
    primary_region = regions[0]
    for _slug, nav_slug, *_ in PAGES:
        flat = FlatPage.objects.filter(region=primary_region, slug=_slug).first()
        if flat is None:
            continue
        NavItem.objects.filter(slug=nav_slug).update(
            flat_page=flat,
            url_name='',
        )


def unseed(apps, schema_editor):
    FlatPage = apps.get_model('pages', 'FlatPage')
    NavItem = apps.get_model('navigation', 'NavItem')

    slugs = [p[0] for p in PAGES]
    NavItem.objects.filter(slug__in=[p[1] for p in PAGES]).update(flat_page=None)
    FlatPage.objects.filter(slug__in=slugs).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0011_flatpage'),
        ('navigation', '0009_navitem_flat_page_alter_navitem_url_name'),
        ('regions', '0002_seed_regions'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
