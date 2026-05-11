from django.db import migrations


# Базовые тексты — общие для регионов (универсальный маркетинг).
# Кастомизируется только бадж и упоминание города в about_body.
COMMON_RU = {
    'hero_title_ru': 'Лучшее образование\nдля будущего вашего\nребёнка',
    'hero_subtitle_ru': 'Международное образование мирового уровня.\n'
                        'Диплом, признаваемый в 125 странах мира',
    'hero_cta_primary_text_ru': 'Поступить сейчас',
    'hero_cta_secondary_text_ru': 'Получить консультацию',
    'about_label_ru': 'Кому подходит',
    'about_title_ru': 'Создаём образовательную\nсреду мирового уровня\nв Казахстане',
}


def about_body(city_name: str) -> str:
    return (
        f'Space School {city_name} — это международная частная школа с космической '
        'концепцией и физико-математическим уклоном. Мы предлагаем программы '
        'Cambridge International Education от Primary до A-Level, готовя учеников '
        'к поступлению в лучшие университеты мира.\n\n'
        'Чтобы развивать критическое мышление, творческий потенциал и глобальное. '
        'У каждого ученика через качественное'
    )


SEEDS = [
    {
        'region_slug': 'astana',
        'fields': {
            **COMMON_RU,
            'hero_badge_text_ru': 'Международная школа в Астанe',
            'about_body_ru': about_body('Astana'),
        },
    },
    {
        'region_slug': 'aktau',
        'fields': {
            **COMMON_RU,
            'hero_badge_text_ru': 'Международная школа в Актау',
            'about_body_ru': about_body('Aktau'),
        },
    },
]


def seed_home_pages(apps, schema_editor):
    Region = apps.get_model('regions', 'Region')
    HomePage = apps.get_model('pages', 'HomePage')

    for seed in SEEDS:
        try:
            region = Region.objects.get(slug=seed['region_slug'])
        except Region.DoesNotExist:
            continue

        # Дефолтное (нелокализованное) значение — копия ru, как требует
        # modeltranslation: пустая base-колонка ломает fallback на чтение.
        ru_fields = seed['fields']
        defaults = {key.removesuffix('_ru'): value for key, value in ru_fields.items()}

        HomePage.objects.update_or_create(
            region=region,
            defaults={**defaults, **ru_fields},
        )


def unseed_home_pages(apps, schema_editor):
    HomePage = apps.get_model('pages', 'HomePage')
    HomePage.objects.filter(
        region__slug__in=[s['region_slug'] for s in SEEDS]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('pages', '0001_initial'),
        ('regions', '0003_alter_region_options'),
    ]
    operations = [
        migrations.RunPython(seed_home_pages, unseed_home_pages),
    ]
