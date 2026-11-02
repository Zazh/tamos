"""Контент трёх ноябрьских событий Астаны (RU) — EF-04.

Источник текстов — DATA билдера Figma (archive/events-landing/block-2-figma/
figma-builders.js: DAY, SKILLS, LEADER); лид Cambridge Day — комментарий
ревьюера дизайна № 1. Идемпотентно: update_or_create по (region, slug),
inline-строки пересоздаются. KK/EN — fallback на RU (заполняют менеджеры).
Ведущие Cambridge Day — админ-состав Астаны на момент выполнения.
"""
from datetime import date, time

from django.db import migrations

# P(start, end, title, text, is_break)
def P(start, end, title, text, is_break=False):
    return (start, end, title, text, is_break)


PAID_LEAD = 'Оставьте имя и телефон: мы перезвоним, подтвердим участие и расскажем об оплате.'

LANDINGS = [
    {
        'slug': 'cambridge-day',
        'is_published': True,
        'is_paid': False,
        'price': None,
        'show_parent_checkbox': False,
        'leaders_from_admins': True,
        'text': {
            'title': 'Cambridge Day',
            'badge_text': 'Для родителей',
            'lead': (
                'Cambridge Day — день открытых дверей Space School, посвящённый '
                'международной программе Cambridge в среднем образовании. Родители и дети '
                'познакомятся со школой, узнают, как устроено обучение по программе, и '
                'попробуют её формат на практике.'
            ),
            'audience_title': 'Для родителей, которые выбирают школу',
            'audience_text': (
                'Родители школьников Астаны, которые рассматривают частное образование '
                'и международные программы.'
            ),
            'goal': (
                'Познакомить родителей с образовательным подходом, академической командой '
                'и школьной средой Space School, ответить на вопросы об обучении и поступлении.'
            ),
            'program_title': 'Программа дня',
            'materials_title': '',
            'leaders_title': 'Кто встретит вас на Cambridge Day',
            'leaders_lead': (
                'Руководство школы, академическая команда и отдел приёма расскажут о '
                'Space School и ответят на вопросы родителей.'
            ),
            'reg_title': 'Регистрация\nна Cambridge Day',
            'reg_text': (
                'Участие бесплатное. Оставьте имя и телефон — мы перезвоним и подтвердим участие'
            ),
            'form_title': 'Регистрация на Cambridge Day',
            'form_lead': (
                'Участие бесплатное. Оставьте имя и телефон: мы перезвоним и подтвердим участие.'
            ),
            'form_note': 'Участие бесплатное, по предварительной регистрации.',
            'cta_text': 'Зарегистрироваться бесплатно',
            'price_note': 'по предварительной регистрации',
        },
        'days': [
            {
                'date': date(2026, 11, 14), 'start': time(11, 0), 'end': time(14, 0), 'label': '',
                'program': [
                    P('11:00', '11:20', 'Регистрация и встреча', 'Сбор вопросов, знакомство с программой дня'),
                    P('11:20', '11:35', 'Открытие Cambridge Day', 'Приветственное слово руководства, представление школы'),
                    P('11:35', '12:05', 'Международное образование', 'Образовательный путь, подходы к преподаванию и оцениванию'),
                    P('12:05', '12:30', 'Обучение в Space School', 'Академическая команда, поддержка учеников, обратная связь родителям'),
                    P('12:30', '13:00', 'Мини-урок для родителей', 'Практическое знакомство с методами обучения'),
                    P('13:00', '13:25', 'Экскурсия по школе', 'Учебные пространства и инфраструктура'),
                    P('13:25', '13:45', 'Диалог с академической командой', 'Вопросы об адаптации, нагрузке, языке обучения и школьной жизни'),
                    P('13:45', '14:00', 'Поступление и дальнейшие шаги', 'Порядок поступления, запись на индивидуальные консультации'),
                ],
            },
        ],
        'materials': [],
        'tiles': [],
    },
    {
        'slug': 'skills-xxi',
        'is_published': False,  # Р-6: черновик, включение — в бэкофисе
        'is_paid': True,
        'price': 18990,
        'show_parent_checkbox': True,
        'leaders_from_admins': False,
        'text': {
            'title': 'Навыки XXI века',
            'badge_text': 'Для родителей',
            'lead': (
                'Как помочь ребёнку научиться учиться. Воркшоп для родителей с практикой '
                'и планом на две недели.'
            ),
            'audience_title': 'Для родителей школьников',
            'audience_text': '',
            'goal': (
                'Познакомить родителей с практическими способами поддержки концентрации, '
                'запоминания, мотивации и самостоятельности ребёнка в учёбе.'
            ),
            'program_title': 'Программа воркшопа',
            'materials_title': '',
            'leaders_title': 'Кто проведёт воркшоп',
            'leaders_lead': 'Ведущего объявим ближе к дате воркшопа.',
            'reg_title': 'Регистрация\nна «Навыки XXI века»',
            'reg_text': (
                '18 990 ₸, родителям Space School — бесплатно. Оставьте имя и телефон — мы '
                'перезвоним, подтвердим участие и расскажем об оплате'
            ),
            'form_title': 'Регистрация на воркшоп',
            'form_lead': PAID_LEAD,
            'form_note': 'Оплата после подтверждения участия.',
            'cta_text': 'Зарегистрироваться · 18 990 ₸',
            'price_note': 'родителям Space School бесплатно',
        },
        'days': [
            {
                'date': date(2026, 11, 21), 'start': time(10, 0), 'end': time(13, 0), 'label': '',
                'program': [
                    P('10:00', '10:15', 'Регистрация и знакомство', 'Ожидания родителей. Какие трудности возникают у ребёнка: отвлекается, быстро забывает материал, откладывает задания или боится ошибок.'),
                    P('10:15', '10:35', 'Зачем ребёнку навыки XXI века', 'Умение применять знания, учиться самостоятельно и справляться с новыми задачами. Роль семьи в развитии этих навыков.'),
                    P('10:35', '11:00', 'Концентрация и организация учёбы', 'Информационная перегрузка, отвлекающие факторы, учебная нагрузка и отдых. Практикум: составление реалистичного плана учебного дня.'),
                    P('11:00', '11:30', 'Как понимать и запоминать материал', 'Связи и ассоциации, осмысленное повторение, сочетание объяснения и практики. Упражнения на запоминание и обсуждение их применения дома.'),
                    P('11:30', '11:40', 'Перерыв', 'Короткий отдых.', True),
                    P('11:40', '12:05', 'Мотивация и целеполагание', 'Как помочь ребёнку поставить посильную цель и разделить её на шаги. Практикум: перевод общей цели в конкретные действия.'),
                    P('12:05', '12:30', 'Ошибки, настойчивость и подготовка к экзаменам', 'Как обсуждать неудачи без обвинений, замечать прогресс и планировать подготовку. Разбор семейных ситуаций.'),
                    P('12:30', '12:50', 'Семейный план действий', 'Выбор двух-трёх приёмов для применения дома. План на ближайшие две недели: действия ребёнка, поддержка родителей, обсуждение результатов.'),
                    P('12:50', '13:00', 'Вопросы и завершение', 'Ответы спикера, обратная связь и итоги.'),
                ],
            },
        ],
        'materials': [],
        'tiles': [],
    },
    {
        'slug': 'cambridge-programme-leader',
        'is_published': True,
        'is_paid': True,
        'price': 50000,
        'show_parent_checkbox': False,
        'leaders_from_admins': False,
        'text': {
            'title': 'Cambridge Programme Leader',
            'badge_text': 'Для педагогов · 2 дня',
            'lead': (
                'От координации к лидерству. Двухдневный семинар-практикум для педагогов '
                'и руководителей школ.'
            ),
            'audience_title': 'Для педагогов и руководителей школ',
            'audience_text': (
                'Педагоги, координаторы международных программ, заместители директоров '
                'и директора школ.'
            ),
            'goal': (
                'Помочь участникам выстроить координацию Cambridge-программы: от учебного '
                'планирования и поддержки педагогов до анализа результатов и управления изменениями.'
            ),
            'program_title': 'Программа семинара',
            'materials_title': 'Материалы участника',
            'leaders_title': 'Кто проведёт семинар',
            'leaders_lead': 'Ведущего объявим ближе к дате семинара.',
            'reg_title': 'Регистрация на семинар\nCambridge Programme Leader',
            'reg_text': (
                '50 000 ₸ за участника за два дня. Оставьте имя и телефон — мы перезвоним, '
                'подтвердим участие и расскажем об оплате'
            ),
            'form_title': 'Регистрация на семинар',
            'form_lead': PAID_LEAD,
            'form_note': 'Оплата после подтверждения участия.',
            'cta_text': 'Зарегистрироваться · 50 000 ₸',
            'price_note': 'за участника за два дня',
        },
        'days': [
            {
                'date': date(2026, 11, 21), 'start': time(9, 30), 'end': time(17, 0),
                'label': 'День 1 · 21 ноября',
                'program': [
                    P('09:00', '09:30', 'Регистрация, приветственный кофе', 'Встреча и знакомство'),
                    P('09:30', '09:50', 'Открытие и самодиагностика школы', 'Ожидания участников, вводная сессия, анкета'),
                    P('09:50', '11:10', 'Модуль 1. Роль координатора', 'Зоны ответственности, распределение функций, годовой цикл. Практикум «Карта ролей школы»'),
                    P('11:10', '11:25', 'Кофе-брейк', '', True),
                    P('11:25', '13:00', 'Модуль 2. Учебные программы', 'Связь ступеней Primary, Lower Secondary, IGCSE и AS & A Level. Практикумы «Линия прогрессии» и «Учебный план школы»'),
                    P('13:00', '14:00', 'Обеденный перерыв', '', True),
                    P('14:00', '15:30', 'Модуль 3. Преподавание и обучение', 'Активное обучение, оценивание в процессе урока. Разбор видеофрагмента по чек-листу'),
                    P('15:30', '15:45', 'Кофе-брейк', '', True),
                    P('15:45', '16:45', 'Модуль 3 — продолжение', 'Конструктивная обратная связь учителю. Ролевая практика'),
                    P('16:45', '17:00', 'Итоги первого дня', 'Рефлексия и вопросы'),
                ],
            },
            {
                'date': date(2026, 11, 22), 'start': time(9, 30), 'end': time(17, 0),
                'label': 'День 2 · 22 ноября',
                'program': [
                    P('09:30', '09:40', 'Начало второго дня', 'Вопросы по первому дню, план работы'),
                    P('09:40', '11:10', 'Модуль 4. Оценивание и данные', 'Внутреннее оценивание, пробные экзамены, анализ результатов и прогнозирование оценок. Практикум «Решения по данным»'),
                    P('11:10', '11:25', 'Кофе-брейк', '', True),
                    P('11:25', '13:00', 'Модуль 5. Лидерство и изменения', 'Развитие команды, вовлечение учителей, коммуникация с родителями. Кейс «Внедрение изменений»'),
                    P('13:00', '14:00', 'Обеденный перерыв', '', True),
                    P('14:00', '15:30', 'Модуль 5 — продолжение', 'План развития программы на год: приоритеты, действия, ответственные, сроки, показатели'),
                    P('15:30', '15:45', 'Кофе-брейк', '', True),
                    P('15:45', '16:30', 'Презентации планов', 'Выступления групп и обратная связь'),
                    P('16:30', '16:50', 'Рефлексия', 'План действий на первые 30 дней, анкета обратной связи'),
                    P('16:50', '17:00', 'Завершение', 'Вручение сертификатов участника'),
                ],
            },
        ],
        'materials': [
            'Рабочая тетрадь',
            'Карта ролей координатора',
            'Схема ступеней Cambridge',
            'Чек-лист наблюдения урока',
            'Шаблон обратной связи учителю',
            'Таблица отслеживания прогресса',
            'Шаблон годового плана',
        ],
        'tiles': [
            ('Язык', 'Русский, термины Cambridge на английском'),
            ('Группа', '20–30 человек'),
        ],
    },
]

SLUGS = [item['slug'] for item in LANDINGS]


def _tr(**fields):
    """Translatable-поля: базовое + _ru (как в pages/0025)."""
    out = {}
    for name, value in fields.items():
        out[name] = value
        out[f'{name}_ru'] = value
    return out


def _parse(hhmm):
    h, m = hhmm.split(':')
    return time(int(h), int(m))


def _minutes(start, end):
    a, b = _parse(start), _parse(end)
    return (b.hour * 60 + b.minute) - (a.hour * 60 + a.minute)


def forward(apps, schema_editor):
    Region = apps.get_model('regions', 'Region')
    TeamMember = apps.get_model('team', 'TeamMember')
    EventLanding = apps.get_model('eventlandings', 'EventLanding')
    Day = apps.get_model('eventlandings', 'EventLandingDay')
    Row = apps.get_model('eventlandings', 'EventLandingProgramRow')
    Material = apps.get_model('eventlandings', 'EventLandingMaterial')
    Tile = apps.get_model('eventlandings', 'EventLandingTile')

    astana = Region.objects.filter(slug='astana').first()
    if astana is None:
        return

    for item in LANDINGS:
        landing, _ = EventLanding.objects.update_or_create(
            region=astana,
            slug=item['slug'],
            defaults={
                'is_published': item['is_published'],
                'is_paid': item['is_paid'],
                'price': item['price'],
                'show_parent_checkbox': item['show_parent_checkbox'],
                **_tr(**item['text']),
            },
        )

        Day.objects.filter(landing=landing).delete()  # строки программы — каскадом
        Material.objects.filter(landing=landing).delete()
        Tile.objects.filter(landing=landing).delete()

        for d in item['days']:
            day = Day.objects.create(
                landing=landing, date=d['date'], start=d['start'], end=d['end'],
                **_tr(label=d['label']),
            )
            for i, (start, end, title, text, is_break) in enumerate(d['program'], start=1):
                Row.objects.create(
                    day=day,
                    start=_parse(start),
                    duration_min=_minutes(start, end),
                    is_break=is_break,
                    order=i * 10,
                    **_tr(title=title, text=text),
                )
        for i, title in enumerate(item['materials'], start=1):
            Material.objects.create(landing=landing, order=i * 10, **_tr(title=title))
        for i, (title, text) in enumerate(item['tiles'], start=1):
            Tile.objects.create(landing=landing, order=i * 10, **_tr(title=title, text=text))

        if item['leaders_from_admins']:
            admins = TeamMember.objects.filter(region=astana, is_admin=True, is_published=True)
            landing.leaders.set(admins)


def reverse(apps, schema_editor):
    EventLanding = apps.get_model('eventlandings', 'EventLanding')
    EventLanding.objects.filter(region__slug='astana', slug__in=SLUGS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('eventlandings', '0001_initial'),
        ('team', '0011_remove_teammember_og_image'),
        ('regions', '0005_seed_inactive_cities'),
    ]

    operations = [
        migrations.RunPython(forward, reverse),
    ]
