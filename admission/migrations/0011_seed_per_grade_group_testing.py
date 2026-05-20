"""Заполняет процедуру тестирования с учётом группы классов.

До этой миграции все варианты (включая 8-11/7-11 senior и 2-7/2-6/2-4 middle)
содержали junior-контент: «20-60 минут, родитель присутствует, результат сразу».
Это не соответствовало реальной процедуре старого сайта, где:
  - 1 класс — родитель присутствует, 20-60 мин, результат сразу
  - 2-8 классы — без родителей, 40-60 мин, +казахский/русский+английский,
    результат в WhatsApp 3 дня
  - 9-11 классы — на английском, математика+английский, 40-60 мин, без родителей

Наша группировка:
  junior = {1}
  middle = {2-7, 2-6, 2-4}
  senior = {8-11, 7-11}

Источник правды — `admission.seed_data` (build_variant_content,
testing_features_for_variant). Применяется идемпотентно ко всем регионам
с AdmissionPage (astana + aktau; inactive almaty/shymkent уже удалены 0009).

Перезаписываются только переключаемые по группе поля:
  - AdmissionVariant: testing_lead, result_intro
  - AdmissionTestingFeature (4 inline на variant): description, title

Не трогаем: h1, hero_lead, result_detail, pricing_lead (там либо общий
текст, либо менеджер мог уже подправить), и pricing_plans (цены —
отдельный разговор).
"""
from django.db import migrations

from admission.seed_data import build_variant_content, testing_features_for_variant


def update_per_group(apps, schema_editor):
    AdmissionVariant = apps.get_model('admission', 'AdmissionVariant')
    AdmissionTestingFeature = apps.get_model('admission', 'AdmissionTestingFeature')

    for variant in AdmissionVariant.objects.select_related('department', 'grade'):
        content = build_variant_content(variant.department.slug, variant.grade.slug)
        variant.testing_lead = content['testing_lead']
        variant.testing_lead_ru = content['testing_lead']
        variant.result_intro = content['result_intro']
        variant.result_intro_ru = content['result_intro']
        variant.save(update_fields=[
            'testing_lead', 'testing_lead_ru',
            'result_intro', 'result_intro_ru',
        ])

        features = testing_features_for_variant(
            variant.department.slug, variant.grade.slug,
        )
        for order, feat in enumerate(features, start=1):
            AdmissionTestingFeature.objects.update_or_create(
                variant=variant, order=order,
                defaults={
                    'icon_svg': feat['icon_svg'],
                    'title': feat['title'],
                    'title_ru': feat['title'],
                    'description': feat['description'],
                    'description_ru': feat['description'],
                },
            )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0010_aktau_two_grade_groups'),
    ]

    operations = [
        migrations.RunPython(update_per_group, noop),
    ]
