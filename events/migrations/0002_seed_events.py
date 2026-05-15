"""Seed мок-мероприятий для двух регионов (Astana + Aktau).

Идея — плоская лента анонсов/отчётов, разный набор в каждом филиале,
чтобы фильтр по региону был наглядно виден.
"""
from datetime import datetime, timezone

from django.db import migrations


def _dt(y, m, d):
    return datetime(y, m, d, 10, 0, tzinfo=timezone.utc)


def _short_html(lead):
    return (
        f'<h2>О мероприятии</h2>\n<p>{lead}</p>\n'
        f'<p>Подробности и регистрация — через форму на странице или по '
        f'телефону приёмной комиссии.</p>'
    )


ASTANA_EVENTS = [
    {
        'slug': 'open-day-spring-2026',
        'title': 'День открытых дверей · весна 2026',
        'lead': 'Приглашаем родителей будущих первоклассников: экскурсия '
                'по школе, презентация программы Cambridge International и '
                'встреча с координаторами поступления.',
        'cover_caption': 'Главный холл Space School Astana',
        'cover_alt': 'Родители на дне открытых дверей',
        'published_at': _dt(2026, 4, 22),
    },
    {
        'slug': 'science-fair-2026',
        'title': 'Школьная научная ярмарка Space Fair',
        'lead': 'Ежегодная выставка ученических исследовательских проектов — '
                'от климата до робототехники. 60 стендов и 200 авторов.',
        'cover_caption': '',
        'cover_alt': '',
        'published_at': _dt(2026, 4, 17),
    },
    {
        'slug': 'mit-alumni-meetup',
        'title': 'Встреча с выпускниками MIT',
        'lead': 'Открытая лекция и Q&A с тремя выпускниками Massachusetts '
                'Institute of Technology, основателями стартапов в США и Сингапуре.',
        'cover_caption': '',
        'cover_alt': '',
        'published_at': _dt(2026, 4, 12),
    },
    {
        'slug': 'spring-concert-2026',
        'title': 'Весенний концерт музыкальной студии',
        'lead': 'Ученики музыкального направления исполняют программу из '
                '«Времён года» Чайковского и современной казахстанской музыки.',
        'cover_caption': '',
        'cover_alt': '',
        'published_at': _dt(2026, 4, 6),
    },
    {
        'slug': 'sat-prep-info-night',
        'title': 'Информационный вечер · подготовка к SAT',
        'lead': 'Презентация новой программы подготовки к SAT для учеников '
                '9–11 классов, расписание занятий и пробные тесты.',
        'cover_caption': '',
        'cover_alt': '',
        'published_at': _dt(2026, 3, 28),
    },
]


AKTAU_EVENTS = [
    {
        'slug': 'open-day-aktau-spring-2026',
        'title': 'День открытых дверей Space School Aktau',
        'lead': 'Экскурсия, знакомство с учителями и презентация программы '
                'Cambridge International для будущих первоклассников.',
        'cover_caption': '',
        'cover_alt': '',
        'published_at': _dt(2026, 4, 19),
    },
    {
        'slug': 'mangistau-sport-festival',
        'title': 'Спортивный фестиваль школ Мангистау',
        'lead': 'Площадка Space School Aktau принимает региональные '
                'соревнования по лёгкой атлетике и волейболу.',
        'cover_caption': '',
        'cover_alt': '',
        'published_at': _dt(2026, 4, 15),
    },
    {
        'slug': 'caspian-eco-expedition',
        'title': 'Экологическая экспедиция «Каспий»',
        'lead': 'Двухдневный выезд на побережье: мониторинг загрязнения '
                'пляжей, лекция океанолога, лабораторная работа.',
        'cover_caption': '',
        'cover_alt': '',
        'published_at': _dt(2026, 4, 9),
    },
    {
        'slug': 'parents-meetup-aktau',
        'title': 'Родительская встреча по итогам триместра',
        'lead': 'Координаторы Cambridge представляют отчёт по успеваемости '
                'и отвечают на вопросы родителей.',
        'cover_caption': '',
        'cover_alt': '',
        'published_at': _dt(2026, 4, 3),
    },
]


def _seed_for_region(apps, region, events):
    Event = apps.get_model('events', 'Event')
    for e in events:
        title = e['title']
        lead = e['lead']
        content = e.get('content_html') or _short_html(lead)
        cover_caption = e.get('cover_caption', '') or ''
        cover_alt = e.get('cover_alt', '') or ''
        Event.objects.update_or_create(
            region=region,
            slug=e['slug'],
            defaults={
                'title': title,
                'title_ru': title,
                'lead': lead,
                'lead_ru': lead,
                'content': content,
                'content_ru': content,
                'cover_caption': cover_caption,
                'cover_caption_ru': cover_caption,
                'cover_alt': cover_alt,
                'cover_alt_ru': cover_alt,
                'is_published': True,
                'published_at': e['published_at'],
            },
        )


def seed(apps, schema_editor):
    Region = apps.get_model('regions', 'Region')
    for slug, events in [('astana', ASTANA_EVENTS), ('aktau', AKTAU_EVENTS)]:
        region = Region.objects.filter(slug=slug).first()
        if region is None:
            continue
        _seed_for_region(apps, region, events)


def unseed(apps, schema_editor):
    Event = apps.get_model('events', 'Event')
    all_slugs = {e['slug'] for e in ASTANA_EVENTS} | {e['slug'] for e in AKTAU_EVENTS}
    Event.objects.filter(slug__in=all_slugs).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0001_initial'),
        ('regions', '0002_seed_regions'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
