"""Seed FlatPage для футерных юридических документов (Политика, Оферта).

В навигацию не попадают — линкуются только из футера через
`{% region_url 'pages:flat' slug='privacy' %}` и `slug='oferta'`.

Идемпотентно (update_or_create по region+slug).
"""
from django.db import migrations


# placeholder-контент: editor наполняет настоящий юридический текст в админке.
PLACEHOLDER_CONTENT = {
    'ru': (
        '<p>Текст документа будет опубликован в ближайшее время. '
        'По вопросам — пишите на странице «Контакты».</p>'
    ),
    'kk': (
        '<p>Құжаттың мәтіні жуырда жарияланады. '
        'Сұрақтар бойынша — «Байланыс» бетіне жазыңыз.</p>'
    ),
    'en': (
        '<p>The document text will be published shortly. '
        'For questions, reach out via the Contacts page.</p>'
    ),
}


PAGES = [
    # slug, ru, kk, en
    ('privacy',
     'Политика конфиденциальности',
     'Құпиялылық саясаты',
     'Privacy policy'),
    ('oferta',
     'Публичная оферта',
     'Жария оферта',
     'Public offer'),
]


def seed(apps, schema_editor):
    Region = apps.get_model('regions', 'Region')
    FlatPage = apps.get_model('pages', 'FlatPage')

    for region in Region.objects.all():
        for slug, ru, kk, en in PAGES:
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


def unseed(apps, schema_editor):
    FlatPage = apps.get_model('pages', 'FlatPage')
    FlatPage.objects.filter(slug__in=[p[0] for p in PAGES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0012_seed_flat_pages'),
        ('regions', '0002_seed_regions'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
