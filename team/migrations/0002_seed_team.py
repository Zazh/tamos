"""Сид мок-данных команды.

Разворачивает состав из 5 человек на регион — директор, академический
директор, инженер-наставник, куратор Cambridge, тренер физмат. Полная
анкета (bio + linkedin) заполняется только для директора Астаны.

Поле resume исторически было — модель TeamResumeItem удалена в 0006,
блок резюме сюда сейчас не пишется.

Идемпотентно: update_or_create по (region, slug).
"""
from django.db import migrations


# (slug, name_ru, role_ru, meta_ru, quote_ru, bio_ru, linkedin_url, resume[(period, title_ru)])
ASTANA_MEMBERS = [
    (
        'aigerim-nurlanova',
        'Айгерим Нурланова',
        'Основатель и директор',
        'PhD в педагогике · 20 лет в международном образовании',
        '«Каждый ребёнок рождён исследователем. Моя задача — создать '
        'среду, где этот огонь не гаснет, а разгорается сильнее с '
        'каждым годом.»',
        '<p>Айгерим — основатель Space School и идеолог образовательной '
        'модели, в которой Cambridge International встречается с глубокой '
        'физмат-подготовкой и космической программой.</p>\n'
        '<p>До запуска школы 12 лет руководила международными программами '
        'в Назарбаев Интеллектуальных школах и провела более 200 семинаров '
        'для учителей по всей Центральной Азии.</p>\n'
        '<h3>Чем занимается в школе</h3>\n'
        '<ul>'
        '<li>Стратегия школы и партнёрства с университетами</li>'
        '<li>Подбор и обучение академической команды</li>'
        '<li>Личные встречи с родителями каждой семьи раз в год</li>'
        '</ul>',
        'https://www.linkedin.com/in/example-nurlanova',
        [
            ('2024 — наст.', 'Основатель и директор Space School'),
            ('2016–2024', 'Заместитель директора по международным программам, НИШ'),
            ('2012–2016', 'Учитель математики, Tashkent International School'),
            ('2010', 'PhD по педагогике, University of Cambridge'),
            ('2006', 'BSc Mathematics, University of Warwick'),
        ],
    ),
    (
        'daniyar-zholdas',
        'Данияр Жолдас',
        'Академический директор',
        'MSc Mathematics, Oxford · 15 лет преподавания',
        '«Хорошая математика — это когда ученик сам формулирует правильный '
        'вопрос. Нашу программу мы строим вокруг этого навыка.»',
        '<p>Данияр отвечает за академическую программу — от учебного плана '
        'Cambridge IGCSE и A-Level до выбора учебников по физмат-блоку.</p>\n'
        '<p>Преподавал математику в школах Великобритании и Казахстана, '
        'готовил победителей IMO и Tournament of Towns.</p>',
        '',
        [
            ('2024 — наст.', 'Академический директор Space School'),
            ('2018–2024', 'Head of Mathematics, Haileybury Astana'),
            ('2012–2018', 'Преподаватель математики, Westminster School (UK)'),
            ('2010', 'MSc Mathematics, University of Oxford'),
        ],
    ),
    (
        'aliya-bekova',
        'Алия Бекова',
        'Куратор Cambridge International',
        'Cambridge Examiner · 10 лет в международной аккредитации',
        '«Cambridge — это не оценки, а язык, на котором весь мир говорит '
        'с университетами. Мы учим этот язык с первого класса.»',
        '',
        '',
        [
            ('2025 — наст.', 'Куратор Cambridge International, Space School'),
            ('2019–2025', 'Cambridge Assessment International Examiner'),
            ('2014–2019', 'IB Coordinator, KAGS International School'),
        ],
    ),
    (
        'arman-toleukhanov',
        'Арман Толеуханов',
        'Инженер-наставник, лаборатория Space',
        'Бывший инженер JAXA · робототехника и космос',
        '',
        '',
        '',
        [
            ('2025 — наст.', 'Инженер-наставник Space School'),
            ('2021–2025', 'Mission engineer, JAXA (Японское космическое агентство)'),
            ('2018–2021', 'PhD Aerospace Engineering, Tokyo Institute of Technology'),
        ],
    ),
    (
        'madina-aibekova',
        'Мадина Айбекова',
        'Тренер физмат-сборной',
        'Тренер национальной команды по физике · IPhO',
        '',
        '',
        '',
        [
            ('2023 — наст.', 'Тренер физмат-сборной Space School'),
            ('2017–2023', 'Тренер национальной сборной Казахстана по физике (IPhO)'),
            ('2015', 'MSc Theoretical Physics, ETH Zürich'),
        ],
    ),
]


# В Актау пока меньше людей — пятеро, но реалистично:
# директор филиала, академ. координатор + 3 наставника.
AKTAU_MEMBERS = [
    (
        'erlan-mukhanov',
        'Ерлан Муханов',
        'Директор Space School Aktau',
        '20 лет в школьном управлении · MBA INSEAD',
        '«Море рядом — но мы смотрим выше. У детей Актау должна быть та '
        'же траектория в мировые университеты, что и у их сверстников '
        'в Астане.»',
        '<p>Ерлан возглавил филиал Space School в Актау в 2024 году. До '
        'этого 12 лет руководил частной школой «Болашак» и провёл '
        'аккредитацию Cambridge International для трёх школ региона.</p>',
        '',
        [
            ('2024 — наст.', 'Директор Space School Aktau'),
            ('2012–2024', 'Директор школы «Болашак», Актау'),
            ('2010', 'MBA, INSEAD'),
        ],
    ),
    (
        'gulnara-ospanova',
        'Гульнара Оспанова',
        'Академический координатор',
        'PhD Education · Cambridge-accredited',
        '«Мы строим маленькую школу с большим вниманием к каждому ребёнку.»',
        '',
        '',
        [
            ('2024 — наст.', 'Академический координатор Space School Aktau'),
            ('2018–2024', 'Заместитель директора, Назарбаев Интеллектуальная школа Актау'),
        ],
    ),
    (
        'timur-aitkali',
        'Тимур Айткали',
        'Учитель математики и наставник',
        'Финалист IMO · 8 лет преподавания',
        '',
        '',
        '',
        [
            ('2024 — наст.', 'Учитель математики, Space School Aktau'),
            ('2018–2024', 'Учитель математики, РФМШ Актау'),
            ('2016', 'BSc Mathematics, Nazarbayev University'),
        ],
    ),
    (
        'aigul-saparova',
        'Айгуль Сапарова',
        'Учитель английского, Cambridge teacher',
        'CELTA + DELTA · 12 лет в международных школах',
        '',
        '',
        '',
        [
            ('2024 — наст.', 'Учитель английского, Space School Aktau'),
            ('2014–2024', 'Senior English teacher, Haileybury Almaty'),
        ],
    ),
    (
        'nurlan-ergaliev',
        'Нурлан Ергалиев',
        'Тренер по робототехнике',
        'WRO Kazakhstan Champion 2022 · 6 лет менторства',
        '',
        '',
        '',
        [
            ('2025 — наст.', 'Тренер по робототехнике, Space School Aktau'),
            ('2019–2025', 'Тренер кружка робототехники, Lyceum №7 Актау'),
            ('2022', 'WRO Kazakhstan — национальный чемпионат, 1 место'),
        ],
    ),
]


def _seed_for_region(apps, region, members):
    TeamMember = apps.get_model('team', 'TeamMember')

    for order, data in enumerate(members, start=1):
        slug, name, role, meta, quote, bio, linkedin, _resume = data
        TeamMember.objects.update_or_create(
            region=region,
            slug=slug,
            defaults={
                'name': name,
                'name_ru': name,
                'role': role,
                'role_ru': role,
                'meta': meta,
                'meta_ru': meta,
                'quote': quote,
                'quote_ru': quote,
                'bio': bio,
                'bio_ru': bio,
                'linkedin_url': linkedin,
                'order': order * 10,
                'is_published': True,
            },
        )


def seed(apps, schema_editor):
    Region = apps.get_model('regions', 'Region')

    astana = Region.objects.filter(slug='astana').first()
    if astana is not None:
        _seed_for_region(apps, astana, ASTANA_MEMBERS)

    aktau = Region.objects.filter(slug='aktau').first()
    if aktau is not None:
        _seed_for_region(apps, aktau, AKTAU_MEMBERS)


def unseed(apps, schema_editor):
    TeamMember = apps.get_model('team', 'TeamMember')
    all_slugs = {m[0] for m in ASTANA_MEMBERS} | {m[0] for m in AKTAU_MEMBERS}
    # Резюме каскадно удалятся через CASCADE на FK.
    TeamMember.objects.filter(slug__in=all_slugs).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('team', '0001_initial'),
        ('regions', '0002_seed_regions'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
