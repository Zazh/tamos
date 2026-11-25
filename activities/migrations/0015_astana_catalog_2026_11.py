"""Актуализация каталога кружков Астаны по PDF ЦДО от 2026-11-25.

Источник — «ЦДО Русский.pdf» и «ЦДО Казахский.pdf» (SPACE COURSE, 13 страниц
каждый). Только регион `astana`; Актау не трогаем. Данные — inline (правило
`process/PROJECT.md`: сид не читается из внешних файлов);
`data/clubs_2026_27_astana.json` остаётся снапшотом миграций 0011–0013.

Дельта к каталогу 0011 (33 кружка → 32):
- сняты с публикации — их нет в новом PDF (не удаляются, менеджер может вернуть);
- 6 новых кружков (языковые — в секции «Академические», как и раньше);
- у 4 кружков пересобраны группы и расписание;
- порядок кружков — как в PDF.

Остальные кружки не трогаются совсем: карточка, описание, группы и их pk.
Тексты действующих кружков в новом PDF не менялись. При расхождении RU- и
KK-файла берём RU (у Баскетбола и Таеквондо в KK-файле расписание другое).
ФИО тренеров не переводим: kk/en = копия ru (см. 0014).

Идемпотентно: кружок ищется в регионе по `name_ru`. Откат = бэкап БД.
"""
from datetime import time

from django.db import migrations


REGION_SLUG = 'astana'
LANGS = ('ru', 'kk', 'en')
ALL_CLASSES = list(range(1, 12))

UNPUBLISH = [
    'Space explorers',
    'Занимательная химия, второй год обучения',
    'Cambridge Maths',
    'Подготовка к SAT Math',
    'Qazaq Talk',
    'Parlez (французский язык)',
    'Сөйле',
]

# Кружки, у которых поменялись только группы. Карточку (название, описание,
# локация) не трогаем — группы и слоты пересоздаются из этого описания.
REGROUP = {
    # Новая группа 5–7 классов; у двух прежних в подписи теперь видны классы.
    'Студия танца': {
        'teacher': {'name': 'Айым', 'phone': '+77075120503'},
        'price': 30000,
        'groups': [
            {
                'label': {
                    'ru': '1–4 класс, первая группа',
                    'kk': '1–4 сынып, бірінші топ',
                    'en': 'Grades 1–4, group 1',
                },
                'classes': [1, 2, 3, 4],
                'schedule': [('tue', '16:00', '17:00'), ('thu', '16:00', '17:00')],
            },
            {
                'label': {
                    'ru': '1–4 класс, вторая группа',
                    'kk': '1–4 сынып, екінші топ',
                    'en': 'Grades 1–4, group 2',
                },
                'classes': [1, 2, 3, 4],
                'schedule': [('tue', '17:00', '18:00'), ('thu', '17:00', '18:00')],
            },
            {
                'classes': [5, 6, 7],
                'schedule': [('mon', '16:00', '17:00'), ('wed', '16:00', '17:00')],
            },
        ],
    },
    # Осталась одна группа: Вт/Чт в PDF больше нет.
    'Шахматы': {
        'teacher': {'name': 'Эрик', 'phone': '+77777423409'},
        'price': 30000,
        'groups': [
            {
                'classes': ALL_CLASSES,
                'schedule': [('mon', '16:00', '17:00'), ('wed', '16:00', '17:00')],
            },
        ],
    },
    # Пн/Ср теперь 16:00–18:00 (было до 17:00) — как в обоих файлах.
    'Space robotics': {
        'teacher': {'name': 'Арман', 'phone': '+77782160591'},
        'price': 40000,
        'groups': [
            {
                'label': {'ru': 'Первая группа', 'kk': 'Бірінші топ', 'en': 'Group 1'},
                'classes': [1, 2, 3, 4, 5, 6],
                'schedule': [('mon', '16:00', '18:00'), ('wed', '16:00', '18:00')],
            },
            {
                'label': {'ru': 'Вторая группа', 'kk': 'Екінші топ', 'en': 'Group 2'},
                'classes': [1, 2, 3, 4, 5, 6],
                'schedule': [('tue', '16:00', '17:00'), ('thu', '16:00', '17:00')],
            },
        ],
    },
    # Группы теперь по уровню (было «старшие/младшие классы», обе Вт/Чт).
    'Fun Chinese': {
        'teacher': {'name': 'Малика', 'phone': '+77711678799'},
        'price': 40000,
        'groups': [
            {
                'label': {
                    'ru': 'Продолжающая группа',
                    'kk': 'Жалғастырушы топ',
                    'en': 'Continuing group',
                },
                'classes': ALL_CLASSES,
                'schedule': [('tue', '16:00', '17:00'), ('thu', '16:00', '17:00')],
            },
            {
                'label': {
                    'ru': 'Начинающая группа',
                    'kk': 'Бастауыш топ',
                    'en': 'Beginner group',
                },
                'classes': ALL_CLASSES,
                'schedule': [('wed', '16:00', '17:00'), ('fri', '16:00', '17:00')],
            },
        ],
    },
}

NEW = [
    {
        'section': 'academic',
        'name': {'ru': 'Вайбкодинг', 'kk': 'Вайбкодинг', 'en': 'Vibe Coding'},
        'location': {
            'ru': 'онлайн и очно в Space School',
            'kk': 'онлайн және Space School-да бетпе-бет',
            'en': 'online and in person at Space School',
        },
        # Фиксированных дней в PDF нет — формат курса описан текстом.
        'description': {
            'ru': '12 занятий: каждую неделю 5 онлайн и 1 очно в Space School.',
            'kk': '12 сабақ: әр апта сайын 5 онлайн және Space School-да 1 оффлайн (бетпе-бет) сабақ.',
            'en': '12 lessons: 5 online and 1 in person at Space School every week.',
        },
        'teacher': {'name': 'Динара', 'phone': '+77051111181'},
        'price': 40000,
        'groups': [
            {'classes': [8, 9, 10, 11], 'schedule': []},
        ],
    },
    {
        'section': 'academic',
        'name': {
            'ru': 'Математический кружок «Пятёрочка»',
            'kk': '«Пятёрочка» математикалық үйірмесі',
            'en': 'Pyaterochka Maths Club',
        },
        'location': '311',
        'description': '',
        'teacher': {'name': 'Марина', 'phone': '+77054565201'},
        'price': 35000,
        'groups': [
            {
                'label': {
                    'ru': '5 класс, русский язык обучения',
                    'kk': '5 сынып, оқыту орыс тілінде',
                    'en': 'Grade 5, Russian-medium',
                },
                'classes': [5],
                'schedule': [('mon', '16:00', '17:00'), ('wed', '16:00', '17:00')],
            },
        ],
    },
    {
        'section': 'academic',
        'name': {
            'ru': 'Казахский язык 2–3 классы',
            'kk': 'Қазақ тілі 2–3 сыныптар',
            'en': 'Kazakh Language, Grades 2–3',
        },
        'location': '214',
        'description': {
            'ru': (
                'Что будет на занятиях?\n'
                '• Чтение и понимание текстов: читаем простые тексты, понимаем их смысл, '
                'отвечаем на вопросы.\n'
                '• Говорим и выражаем свои мысли: учимся говорить красиво и грамотно, '
                'отвечаем на вопросы, составляем диалоги.\n'
                '• Грамматика простым языком: изучаем части речи, правильно используем '
                'слова и окончания, строим предложения.\n'
                '• Составляем свои тексты: пишем небольшие рассказы, сочиняем на заданные '
                'темы, расширяем словарный запас.\n'
                '• Диктанты, изложения и сочинения: развиваем грамотность, учимся писать '
                'без ошибок, выражаем свои мысли в письменной форме.\n'
                '• Играем и открываем новое: космические задания, увлекательные игры, '
                'творческие проекты.'
            ),
            'kk': (
                'Сабақтарда не болады?\n'
                '• Мәтіндерді оқу және түсіну: қарапайым мәтіндерді оқимыз, мағынасын '
                'түсінеміз, сұрақтарға жауап береміз.\n'
                '• Сөйлеу және ойды білдіру: әдемі және сауатты сөйлеуді үйренеміз, '
                'сұрақтарға жауап береміз, диалогтар құрамыз.\n'
                '• Грамматика қарапайым тілмен: сөз таптарын үйренеміз, сөздерді және '
                'жалғауларды дұрыс қолданамыз, сөйлемдер құраймыз.\n'
                '• Өз мәтіндерімізді құрастыру: шағын әңгімелер жазамыз, берілген '
                'тақырыптарға шығарма жазамыз, сөздік қорды кеңейтеміз.\n'
                '• Диктанттар, мазмұндамалар және шығармалар: сауаттылықты дамытамыз, '
                'қатесіз жазуды үйренеміз, ойларымызды жазбаша білдіреміз.\n'
                '• Ойнау және жаңалық ашу: ғарыштық тапсырмалар, қызықты ойындар, '
                'шығармашылық жобалар.'
            ),
            'en': (
                'What happens in class?\n'
                '• Reading and comprehension: we read simple texts, understand their '
                'meaning and answer questions.\n'
                '• Speaking and expressing ideas: we learn to speak clearly and correctly, '
                'answer questions and build dialogues.\n'
                '• Grammar made simple: we study parts of speech, use words and endings '
                'correctly and build sentences.\n'
                '• Writing our own texts: we write short stories, compose on given topics '
                'and expand our vocabulary.\n'
                '• Dictations, retellings and essays: we develop literacy, learn to write '
                'without mistakes and express our thoughts in writing.\n'
                '• Playing and discovering: space-themed tasks, exciting games and '
                'creative projects.'
            ),
        },
        'teacher': {'name': 'Айнұр', 'phone': '+77479079518'},
        'price': 30000,
        'groups': [
            {
                'classes': [2, 3],
                'schedule': [('tue', '16:00', '17:00'), ('thu', '16:00', '17:00')],
            },
        ],
    },
    {
        'section': 'academic',
        'name': {
            'ru': 'Английский язык 1–2 классы',
            'kk': 'Ағылшын тілі 1–2 сыныптар',
            'en': 'English, Grades 1–2',
        },
        'location': '103',
        'description': {
            'ru': (
                'На занятиях ребёнок научится:\n'
                '• уверенно читать по-английски;\n'
                '• писать короткие предложения;\n'
                '• отвечать на простые вопросы.'
            ),
            'kk': (
                'Сабақ барысында бала:\n'
                '• ағылшын тілінде еркін әрі сенімді оқуды үйренеді;\n'
                '• қысқа сөйлемдер жазуды меңгереді;\n'
                '• қарапайым сұрақтарға ағылшын тілінде жауап беруді үйренеді.'
            ),
            'en': (
                'In class your child will learn to:\n'
                '• read English with confidence;\n'
                '• write short sentences;\n'
                '• answer simple questions.'
            ),
        },
        'teacher': {'name': 'Ұланай', 'phone': '+77002625668'},
        'price': 35000,
        'groups': [
            {
                'classes': [1, 2],
                'schedule': [('mon', '16:00', '17:00'), ('wed', '16:00', '17:00')],
            },
        ],
    },
    {
        'section': 'academic',
        'name': 'Cambridge English',
        'location': '201',
        'description': {
            'ru': (
                'Что будем делать?\n'
                '• Развивать все языковые навыки (Reading, Writing, Listening, Use of English).\n'
                '• Разбирать типы заданий Cambridge Lower Secondary Checkpoint.\n'
                '• Осваивать стратегии и техники выполнения экзаменационных заданий.\n'
                '• Работать над пробелами в знаниях и повышать уверенность в использовании '
                'английского.'
            ),
            'kk': (
                'Не істейміз?\n'
                '• Барлық тілдік дағдыларды (Reading, Writing, Listening, Use of English) '
                'дамытамыз.\n'
                '• Cambridge Lower Secondary Checkpoint тапсырмаларының түрлерін талдаймыз.\n'
                '• Емтихан тапсырмаларын орындау стратегиялары мен техникаларын меңгереміз.\n'
                '• Білімдегі олқылықтармен жұмыс істеп, ағылшын тілін қолданудағы '
                'сенімділікті арттырамыз.'
            ),
            'en': (
                'What will we do?\n'
                '• Develop all language skills (Reading, Writing, Listening, Use of English).\n'
                '• Work through Cambridge Lower Secondary Checkpoint task types.\n'
                '• Master strategies and techniques for exam tasks.\n'
                '• Close knowledge gaps and build confidence in using English.'
            ),
        },
        'teacher': {'name': 'Юлия', 'phone': '+77078042442'},
        'price': 40000,
        'groups': [
            {
                'classes': [7, 8],
                'schedule': [('mon', '16:00', '16:50'), ('wed', '16:00', '16:50')],
            },
        ],
    },
    {
        'section': 'creative',
        'name': {
            'ru': 'Эстрадное пение',
            'kk': 'Эстрадалық ән айту',
            'en': 'Pop Singing',
        },
        'location': '207',
        'description': {
            'ru': (
                'Что ждёт детей на занятиях:\n'
                '• профессиональные распевки и упражнения для голоса;\n'
                '• развитие слуха, чувства ритма и музыкальности;\n'
                '• навыки пения в ансамбле;\n'
                '• разнообразный репертуар: эстрадные хиты, современные песни и казахские '
                'народные песни;\n'
                '• развитие сценического артистизма и уверенности в себе.'
            ),
            'kk': (
                'Сабақта не үйренеміз:\n'
                '• дауысқа арналған кәсіби жаттығулар мен дауыс ашу;\n'
                '• есту қабілетін, ырғақ сезімін және музыкалық әлеуетті дамыту;\n'
                '• ансамбльде ән айту дағдылары;\n'
                '• әртүрлі бағыттағы репертуар: эстрадалық хиттер, заманауи әндер және '
                'қазақ халық әндері;\n'
                '• сахналық артистизм және өз-өзіне деген сенімділік.'
            ),
            'en': (
                'What awaits children in class:\n'
                '• professional vocal warm-ups and voice exercises;\n'
                '• developing an ear for music, a sense of rhythm and musicality;\n'
                '• ensemble singing skills;\n'
                '• a varied repertoire: pop hits, contemporary songs and Kazakh folk songs;\n'
                '• developing stage presence and self-confidence.'
            ),
        },
        'teacher': {'name': 'Аслан', 'phone': '+77756184760'},
        'price': 30000,
        'groups': [
            {
                'classes': ALL_CLASSES,
                'schedule': [('wed', '16:00', '17:00'), ('fri', '16:00', '17:00')],
            },
        ],
    },
]

# Порядок опубликованных кружков — как в PDF (секция за секцией).
ORDER = [
    # Спортивные
    'Баскетбол',
    'Футбол',
    'Настольный теннис',
    'Студия танца',
    'Таеквондо',
    'Шахматы',
    # Академические
    'Dream Hub — портфолио и развитие',
    'Юный исследователь',
    'Мастер экспериментов',
    'Химик-следопыт',
    'Юный химик-аналитик',
    'Продвинутый химик',
    'IGCSE Chemistry (tips & tricks)',
    'IGCSE Physics Preparation Club',
    'Робототехника и STEM',
    'Space robotics',
    'Решение задач на смекалку',
    'Наследники Евклида',
    'Вайбкодинг',
    'Математический кружок «Пятёрочка»',
    # Языковые (в PDF отдельная страница, на сайте — в «Академических»)
    'Situational speaking',
    'Fun Chinese',
    'Казахский язык 2–3 классы',
    'Английский язык 1–2 классы',
    'Cambridge English',
    # Творческие
    'Глинотерапия',
    'Творческая студия «Колибри»',
    'Арт-терапия',
    'Craft&Design',
    'Гончарное искусство',
    'Живопись',
    'Эстрадное пение',
]


def _parse_time(s):
    h, m = s.split(':')
    return time(int(h), int(m))


def _set_i18n(obj, base, values):
    """values: dict ru/kk/en или строка (одно значение на все языки)."""
    if isinstance(values, str):
        values = {lang: values for lang in LANGS}
    setattr(obj, base, values.get('ru', '') or '')
    for lang in LANGS:
        setattr(obj, f'{base}_{lang}', values.get(lang, '') or '')


def _rebuild_groups(Group, Slot, activity, club):
    """Группы и слоты кружка — с нуля из описания."""
    activity.groups.all().delete()
    teacher = club['teacher']
    for g_order, g in enumerate(club['groups'], start=1):
        group = Group(activity=activity, order=g_order * 10)
        _set_i18n(group, 'label', g.get('label', ''))
        _set_i18n(group, 'teacher_name', teacher['name'])
        group.teacher_phone = teacher['phone']
        _set_i18n(group, 'teacher_bio', '')
        group.classes = list(g['classes'])
        group.price = club['price']
        group.students_status = 'recruiting'
        group.min_students = 5
        group.max_students = 20
        group.save()
        for s_order, (day, start, end) in enumerate(g['schedule'], start=1):
            Slot.objects.create(
                group=group,
                day=day,
                start_time=_parse_time(start),
                end_time=_parse_time(end),
                order=s_order * 10,
            )


def update_catalog(apps, schema_editor):
    Region = apps.get_model('regions', 'Region')
    Section = apps.get_model('activities', 'ActivitySection')
    Activity = apps.get_model('activities', 'Activity')
    Group = apps.get_model('activities', 'ActivityGroup')
    Slot = apps.get_model('activities', 'ScheduleSlot')

    region = Region.objects.filter(slug=REGION_SLUG).first()
    if region is None:
        return
    in_region = Activity.objects.filter(region=region)

    in_region.filter(name_ru__in=UNPUBLISH).update(is_published=False, is_featured=False)

    for name, club in REGROUP.items():
        activity = in_region.filter(name_ru=name, is_published=True).order_by('order', 'pk').first()
        if activity is None:
            # Кружок переименовали или сняли в бэкофисе — не угадываем.
            print(f'\n  activities.0015: кружок «{name}» не найден в Астане — группы не обновлены')
            continue
        _rebuild_groups(Group, Slot, activity, club)

    for club in NEW:
        names = club['name'] if isinstance(club['name'], dict) else {'ru': club['name']}
        activity = (
            in_region.filter(name_ru=names['ru']).order_by('-is_published', 'order', 'pk').first()
            or Activity(region=region)
        )
        activity.section = Section.objects.get(slug=club['section'])
        _set_i18n(activity, 'name', club['name'])
        _set_i18n(activity, 'location', club['location'])
        _set_i18n(activity, 'description', club['description'])
        activity.is_published = True
        activity.save()
        _rebuild_groups(Group, Slot, activity, club)

    for position, name in enumerate(ORDER, start=1):
        in_region.filter(name_ru=name, is_published=True).update(order=position * 10)


def noop(apps, schema_editor):
    """Откат = восстановление из бэкапа БД; обратной трансформации нет."""


class Migration(migrations.Migration):
    dependencies = [
        ('activities', '0014_teacher_names_no_translit'),
        ('regions', '0005_seed_inactive_cities'),
    ]
    operations = [
        migrations.RunPython(update_catalog, noop),
    ]
