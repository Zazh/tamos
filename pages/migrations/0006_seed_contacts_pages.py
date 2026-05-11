from django.db import migrations


# Базовые тексты intro — общие для регионов. Office_name/office_address
# подставляются по городу в SEEDS. Department-блоки тоже общие
# (одинаковые маркетинг + контакты) — реальные телефоны/email
# различаются от региона к региону, менеджер допишет в админке.

INTRO_RU = {
    'intro_title_ru': 'Контакты',
    'intro_text_ru': 'Мы всегда на связи — приходите на экскурсию, задавайте вопросы '
                     'или просто позвоните. Выберите удобный способ связи.',
}

OFFICE_HOURS_RU = 'Пн–Пт, 09:00–18:00'


SEEDS = [
    {
        'region_slug': 'astana',
        'fields': {
            **INTRO_RU,
            'office_name_ru': 'Space School Astana',
            'office_address_ru': 'г. Астана, пр. Туран 89/1 район Есиль, 010000',
            'office_hours_ru': OFFICE_HOURS_RU,
            'map_embed': '',
        },
    },
    {
        'region_slug': 'aktau',
        'fields': {
            **INTRO_RU,
            'office_name_ru': 'Space School Aktau',
            'office_address_ru': 'г. Актау, адрес офиса',
            'office_hours_ru': OFFICE_HOURS_RU,
            'map_embed': '',
        },
    },
]


# (slug-ключ для идемпотентности — order; в реальности
# update_or_create по (contacts_page, order). Слаги не нужны: отделы — flat list.)
DEPARTMENTS = [
    {
        'order': 10,
        'title_ru': 'Поступление',
        'description_ru': 'Запись на тестирование, собеседование, консультация '
                          'по программам и стоимости обучения.',
        'phone': '+7 705 111 11 81',
        'email': 'admission@spaceschool.edu.kz',
        'hours_ru': OFFICE_HOURS_RU,
    },
    {
        'order': 20,
        'title_ru': 'Партнёрство',
        'description_ru': 'Сотрудничество с вузами, корпоративные партнёры, '
                          'совместные мероприятия и программы обмена.',
        'phone': '+7 775 888 26 67',
        'email': 'partners@spaceschool.edu.kz',
        'hours_ru': OFFICE_HOURS_RU,
    },
    {
        'order': 30,
        'title_ru': 'Вакансии',
        'description_ru': 'Открытые позиции для педагогов и администрации. '
                          'Резюме принимаются на указанный email.',
        'phone': '+7 771 222 56 52',
        'email': 'hrtamosspace@gmail.com',
        'hours_ru': OFFICE_HOURS_RU,
    },
]


def _with_base(ru_fields: dict) -> dict:
    """Скопировать `*_ru` поля в base-колонки (modeltranslation fallback)."""
    base = {key.removesuffix('_ru'): value
            for key, value in ru_fields.items()
            if key.endswith('_ru')}
    return {**base, **ru_fields}


def seed_contacts_pages(apps, schema_editor):
    Region = apps.get_model('regions', 'Region')
    ContactsPage = apps.get_model('pages', 'ContactsPage')
    ContactsDepartment = apps.get_model('pages', 'ContactsDepartment')

    for seed in SEEDS:
        try:
            region = Region.objects.get(slug=seed['region_slug'])
        except Region.DoesNotExist:
            continue

        defaults = _with_base(seed['fields'])
        contacts, _ = ContactsPage.objects.update_or_create(
            region=region,
            defaults=defaults,
        )

        for dept in DEPARTMENTS:
            dept_defaults = _with_base({
                'title_ru': dept['title_ru'],
                'description_ru': dept['description_ru'],
                'hours_ru': dept['hours_ru'],
            })
            dept_defaults.update({
                'phone': dept['phone'],
                'email': dept['email'],
            })
            ContactsDepartment.objects.update_or_create(
                contacts_page=contacts,
                order=dept['order'],
                defaults=dept_defaults,
            )


def unseed_contacts_pages(apps, schema_editor):
    ContactsPage = apps.get_model('pages', 'ContactsPage')
    ContactsPage.objects.filter(
        region__slug__in=[s['region_slug'] for s in SEEDS]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('pages', '0005_contactspage_contactsdepartment'),
        ('regions', '0005_seed_inactive_cities'),
    ]
    operations = [
        migrations.RunPython(seed_contacts_pages, unseed_contacts_pages),
    ]
