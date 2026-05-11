from django.db import migrations


# Структура повторяет текущую разметку partials/header.html.
# url_name заполнен только у пунктов с реализованными view; остальные —
# заглушки (href="#"). По мере реализации страниц заполняем url_name
# через админку или новую data-миграцию.

SECTIONS = [
    {
        'slug': 'main',
        'order': 10,
        'label_ru': 'Меню',
        'label_kk': 'Мәзір',
        'label_en': 'Menu',
    },
    {
        'slug': 'school-life',
        'order': 20,
        'label_ru': 'Жизнь школы',
        'label_kk': 'Мектеп өмірі',
        'label_en': 'School life',
    },
]


ITEMS = [
    # section_slug, slug, url_name, is_top_nav, order, labels(ru/kk/en)
    ('main', 'home', 'pages:home', True, 10, 'Главная', 'Басты бет', 'Home'),
    ('main', 'about', '', True, 20, 'О нас', 'Біз туралы', 'About us'),
    ('main', 'program', '', True, 30, 'Программа', 'Бағдарлама', 'Programme'),
    ('main', 'admission', '', True, 40, 'Поступление', 'Қабылдау', 'Admission'),
    ('main', 'extracurricular', '', False, 50, 'Внеклассные занятия', 'Сыныптан тыс сабақтар', 'Extracurricular'),
    ('main', 'contacts', 'pages:contacts', False, 60, 'Контакты', 'Байланыс', 'Contacts'),

    ('school-life', 'school-day', '', False, 10, 'Один день в школе', 'Мектептегі бір күн', 'A day at school'),
    ('school-life', 'safety', '', False, 20, 'Безопасность', 'Қауіпсіздік', 'Safety'),
    ('school-life', 'gallery', 'pages:gallery', False, 30, 'Фотогалерея', 'Фотогалерея', 'Gallery'),
    ('school-life', 'uniform', '', False, 40, 'Школьная форма', 'Мектеп формасы', 'Uniform'),
    ('school-life', 'supplies', '', False, 50, 'Школьные принадлежности', 'Мектеп құралдары', 'Supplies'),
    ('school-life', 'food', '', False, 60, 'Питание', 'Тамақтану', 'Meals'),
    ('school-life', 'transport', '', False, 70, 'Операторы развозки', 'Тасымалдау', 'Transport'),
    ('school-life', 'blog', '', False, 80, 'Блог', 'Блог', 'Blog'),
]


def seed_navigation(apps, schema_editor):
    NavSection = apps.get_model('navigation', 'NavSection')
    NavItem = apps.get_model('navigation', 'NavItem')

    sections_by_slug = {}
    for s in SECTIONS:
        section, _ = NavSection.objects.update_or_create(
            slug=s['slug'],
            defaults={
                'order': s['order'],
                'label': s['label_ru'],
                'label_ru': s['label_ru'],
                'label_kk': s['label_kk'],
                'label_en': s['label_en'],
            },
        )
        sections_by_slug[s['slug']] = section

    for section_slug, slug, url_name, is_top, order, ru, kk, en in ITEMS:
        NavItem.objects.update_or_create(
            slug=slug,
            defaults={
                'section': sections_by_slug[section_slug],
                'label': ru,
                'label_ru': ru,
                'label_kk': kk,
                'label_en': en,
                'url_name': url_name,
                'is_top_nav': is_top,
                'order': order,
                'is_published': True,
            },
        )


def unseed_navigation(apps, schema_editor):
    NavSection = apps.get_model('navigation', 'NavSection')
    NavSection.objects.filter(slug__in=[s['slug'] for s in SECTIONS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('navigation', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(seed_navigation, unseed_navigation),
    ]
