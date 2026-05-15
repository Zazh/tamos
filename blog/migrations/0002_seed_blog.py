"""Seed мок-данных блога для двух регионов (Astana + Aktau).

Идея: показать разный контент per-region — в Астане 6 статей (включая
полную MIT-стажировку из прототипа `blog-detail.html`), в Актау 4
региональные новости. Категории и теги — region-scoped, заводятся
отдельно в каждом регионе.

Идемпотентно: update_or_create по (region, slug).
"""
from datetime import datetime, timezone

from django.db import migrations


# ---------------------------------------------------------------------------
# Категории — одинаковая схема в обоих регионах (slug → переводы).
# ---------------------------------------------------------------------------
CATEGORIES = [
    ('school-life', 10, {
        'ru': 'Школьная жизнь',
        'kk': 'Мектеп өмірі',
        'en': 'School life',
    }),
    ('sports', 20, {
        'ru': 'Спорт',
        'kk': 'Спорт',
        'en': 'Sports',
    }),
    ('achievements', 30, {
        'ru': 'Достижения',
        'kk': 'Жетістіктер',
        'en': 'Achievements',
    }),
    ('robotics', 40, {
        'ru': 'Робототехника',
        'kk': 'Робототехника',
        'en': 'Robotics',
    }),
    ('events', 50, {
        'ru': 'Мероприятие',
        'kk': 'Іс-шара',
        'en': 'Events',
    }),
]


# ---------------------------------------------------------------------------
# Теги — берём из blog-detail.html (#MIT, #Достижения, #Исследования, #STEM)
# плюс пара общих. Те же slugs в обоих регионах.
# ---------------------------------------------------------------------------
TAGS = [
    ('mit', {'ru': 'MIT', 'kk': 'MIT', 'en': 'MIT'}),
    ('achievements', {'ru': 'Достижения', 'kk': 'Жетістіктер', 'en': 'Achievements'}),
    ('research', {'ru': 'Исследования', 'kk': 'Зерттеулер', 'en': 'Research'}),
    ('stem', {'ru': 'STEM', 'kk': 'STEM', 'en': 'STEM'}),
    ('school-life', {'ru': 'Школьная жизнь', 'kk': 'Мектеп өмірі', 'en': 'School life'}),
    ('robotics', {'ru': 'Робототехника', 'kk': 'Робототехника', 'en': 'Robotics'}),
]


# ---------------------------------------------------------------------------
# Полный HTML-контент статьи про MIT — из spaceschool/pages/blog-detail.html
# (без gallery-shortcode, который требует Alpine-инициализации).
# ---------------------------------------------------------------------------
MIT_CONTENT_HTML = """
<p>
  В марте 2025 года пятеро учеников Space School Astana стали участниками
  уникальной научной программы Массачусетского технологического института.
  Две недели интенсивной работы в лабораториях MIT изменили их
  представление о том, что значит заниматься наукой.
</p>

<h2>Как устроена программа</h2>
<p>
  Программа построена вокруг трёх лабораторий: Media Lab, CSAIL и Bio.
  Каждый ученик за две недели проходит через все три направления и
  работает в команде с аспирантами MIT над живыми исследовательскими
  задачами.
</p>

<p>
  Отбор на программу — конкурсный, через олимпиады по математике и
  физике. Подробнее о приёмной кампании читайте на странице поступления,
  а актуальные даты — в новостях школы.
</p>

<h3>Что входит в стажировку</h3>
<ul>
  <li>Работа в одной из трёх лабораторий MIT под руководством наставника</li>
  <li>Еженедельные семинары с приглашёнными учёными</li>
  <li>Финальная защита проекта перед комиссией факультета</li>
  <li>Сертификат участия и письмо-рекомендация</li>
</ul>

<blockquote>
  <p>«Мы хотели, чтобы ребята поняли: настоящая наука — это не идеальный
  эксперимент с первого раза, а сотни итераций, в которых ты ошибаешься
  быстрее, чем успеваешь думать».</p>
  <cite>Айгуль Сарсенова, координатор программы Space School</cite>
</blockquote>

<p>
  <small>* Стажировка проводится при поддержке MIT-Kazakhstan Foundation.
  Расходы на перелёт и проживание покрывает грант.</small>
</p>

<p>
  После возвращения участники программы продолжают исследования уже в
  Space School — школа выделяет под это два часа в неделю и доступ к
  лабораторному оборудованию.
</p>
""".strip()


def _short_html(lead):
    """Простой HTML-блок из лида: h2 + параграф. Для постов, у которых
    нет полного контента в верстке — даёт что-то живое в детальной."""
    return (
        f'<h2>Подробнее</h2>\n<p>{lead}</p>\n'
        f'<p>Следите за новостями школы — мы публикуем обновления каждую '
        f'неделю в этом разделе.</p>'
    )


def _dt(y, m, d):
    return datetime(y, m, d, 10, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Посты — Astana (6 шт), берём с прототипа blog-list.html + полную статью
# из blog-detail.html на 4-й позиции.
# ---------------------------------------------------------------------------
ASTANA_POSTS = [
    {
        'slug': 'nauryz-in-school',
        'category': 'school-life',
        'tags': ['school-life'],
        'title': 'Как мы празднуем Наурыз в школе',
        'lead': 'Юрты, бесбармак, спортивные состязания и национальные '
                'игры — рассказываем, как Space School встречает весну.',
        'published_at': _dt(2026, 4, 20),
    },
    {
        'slug': 'math-olympiad-results',
        'category': 'achievements',
        'tags': ['achievements'],
        'title': 'Итоги международной олимпиады по математике',
        'lead': 'Команда Space School привезла из Сингапура три золотых, '
                'две серебряных и серебро в командном зачёте.',
        'published_at': _dt(2026, 4, 18),
    },
    {
        'slug': 'robotics-new-course',
        'category': 'robotics',
        'tags': ['robotics', 'stem'],
        'title': 'Новый курс по робототехнике для средних классов',
        'lead': 'С сентября в Space School стартует курс по робототехнике '
                'для 5–8 классов: Arduino, 3D-печать и автономные роботы.',
        'published_at': _dt(2026, 4, 15),
    },
    {
        'slug': 'mit-internship',
        'category': 'achievements',
        'tags': ['mit', 'achievements', 'research', 'stem'],
        'title': 'Ученики Space School прошли стажировку в MIT: когда наука '
                 'объединяет мир',
        'lead': 'Пятеро учеников две недели работали в лабораториях Media '
                'Lab, CSAIL и Bio под руководством аспирантов MIT.',
        'cover_caption': 'Лаборатория Media Lab, MIT — март 2025',
        'cover_alt': 'Ученики Space School в лаборатории MIT',
        'content_html': MIT_CONTENT_HTML,
        'published_at': _dt(2026, 3, 26),
    },
    {
        'slug': 'sat-preparation-launched',
        'category': 'events',
        'tags': ['stem'],
        'title': 'Программа подготовки к SAT запущена',
        'lead': 'Ученики старших классов получают доступ к структурированной '
                'программе SAT с пробными тестами раз в две недели.',
        'published_at': _dt(2026, 4, 10),
    },
    {
        'slug': 'help-child-love-reading',
        'category': 'school-life',
        'tags': ['school-life'],
        'title': 'Как помочь ребёнку полюбить чтение',
        'lead': 'Школьный библиотекарь Space School делится практическими '
                'советами для родителей.',
        'published_at': _dt(2026, 4, 5),
    },
]


# ---------------------------------------------------------------------------
# Посты — Aktau (4 шт), региональный мок чтобы фильтр по региону
# был наглядно виден: контент про Актау, частично пересекающиеся
# категории/теги, но другие slugs и даты.
# ---------------------------------------------------------------------------
AKTAU_POSTS = [
    {
        'slug': 'nauryz-aktau',
        'category': 'school-life',
        'tags': ['school-life'],
        'title': 'Наурыз в Space School Aktau: морской ветер и юрты',
        'lead': 'Ученики Space School Aktau отметили Наурыз на побережье '
                'Каспия — концерт, спортивные игры и национальная кухня.',
        'published_at': _dt(2026, 4, 21),
    },
    {
        'slug': 'sports-festival-aktau',
        'category': 'sports',
        'tags': ['school-life'],
        'title': 'Спортивный фестиваль школ Мангистау',
        'lead': 'Команда Space School Aktau взяла первое место в эстафете '
                '4×100 и второе — в командном волейболе.',
        'published_at': _dt(2026, 4, 16),
    },
    {
        'slug': 'robotics-club-aktau',
        'category': 'robotics',
        'tags': ['robotics', 'stem'],
        'title': 'В Актау открылся кружок робототехники',
        'lead': 'Space School Aktau запускает новый кружок для 4–7 классов: '
                'Lego Mindstorms, основы программирования, выезды на '
                'республиканские соревнования.',
        'published_at': _dt(2026, 4, 14),
    },
    {
        'slug': 'open-doors-aktau',
        'category': 'events',
        'tags': ['school-life'],
        'title': 'День открытых дверей Space School Aktau',
        'lead': 'Приглашаем родителей будущих первоклассников на день '
                'открытых дверей: экскурсия, знакомство с учителями, '
                'презентация программы Cambridge International.',
        'published_at': _dt(2026, 4, 8),
    },
]


def _seed_for_region(apps, region):
    BlogCategory = apps.get_model('blog', 'BlogCategory')
    BlogTag = apps.get_model('blog', 'BlogTag')
    BlogPost = apps.get_model('blog', 'BlogPost')

    cat_by_slug = {}
    for slug, order, names in CATEGORIES:
        obj, _ = BlogCategory.objects.update_or_create(
            region=region,
            slug=slug,
            defaults={
                'name': names['ru'],
                'name_ru': names['ru'],
                'name_kk': names['kk'],
                'name_en': names['en'],
                'order': order,
            },
        )
        cat_by_slug[slug] = obj

    tag_by_slug = {}
    for slug, names in TAGS:
        obj, _ = BlogTag.objects.update_or_create(
            region=region,
            slug=slug,
            defaults={
                'name': names['ru'],
                'name_ru': names['ru'],
                'name_kk': names['kk'],
                'name_en': names['en'],
            },
        )
        tag_by_slug[slug] = obj

    posts = ASTANA_POSTS if region.slug == 'astana' else AKTAU_POSTS
    for post_data in posts:
        content = post_data.get('content_html') or _short_html(post_data['lead'])
        title = post_data['title']
        lead = post_data['lead']
        obj, _ = BlogPost.objects.update_or_create(
            region=region,
            slug=post_data['slug'],
            defaults={
                'category': cat_by_slug[post_data['category']],
                'title': title,
                'title_ru': title,
                'lead': lead,
                'lead_ru': lead,
                'content': content,
                'content_ru': content,
                'cover_caption': post_data.get('cover_caption', ''),
                'cover_caption_ru': post_data.get('cover_caption', ''),
                'cover_alt': post_data.get('cover_alt', ''),
                'cover_alt_ru': post_data.get('cover_alt', ''),
                'is_published': True,
                'published_at': post_data['published_at'],
            },
        )
        obj.tags.set([tag_by_slug[t] for t in post_data['tags']])


def seed(apps, schema_editor):
    Region = apps.get_model('regions', 'Region')
    for slug in ('astana', 'aktau'):
        region = Region.objects.filter(slug=slug).first()
        if region is None:
            # На пустой базе регионы должны существовать после
            # regions/0002_seed_regions; если нет — пропускаем тихо.
            continue
        _seed_for_region(apps, region)


def unseed(apps, schema_editor):
    BlogPost = apps.get_model('blog', 'BlogPost')
    BlogCategory = apps.get_model('blog', 'BlogCategory')
    BlogTag = apps.get_model('blog', 'BlogTag')
    all_post_slugs = {p['slug'] for p in ASTANA_POSTS} | {p['slug'] for p in AKTAU_POSTS}
    BlogPost.objects.filter(slug__in=all_post_slugs).delete()
    BlogCategory.objects.filter(slug__in=[c[0] for c in CATEGORIES]).delete()
    BlogTag.objects.filter(slug__in=[t[0] for t in TAGS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_initial'),
        ('regions', '0002_seed_regions'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
