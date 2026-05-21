"""Заполняет ВСЕ варианты (не только grade-1) контентом: lead-тексты,
4 testing-features и 3 pricing-plans. Источник правды — `admission.seed_data`.

Идемпотентно: использует update_or_create по (variant, order). Если менеджер
уже редактировал текст вариантa в админке — миграция перезапишет ru-поля
(но трогает только ru — поэтому kk/en правки переживут).
"""
from django.db import migrations

from admission.seed_data import PRICING_PLANS, TESTING_FEATURES, build_variant_content


def seed_all(apps, schema_editor):
    AdmissionVariant = apps.get_model('admission', 'AdmissionVariant')
    AdmissionTestingFeature = apps.get_model('admission', 'AdmissionTestingFeature')
    AdmissionPricingPlan = apps.get_model('admission', 'AdmissionPricingPlan')

    for variant in AdmissionVariant.objects.select_related('department', 'grade'):
        content = build_variant_content(variant.department.slug, variant.grade.slug)
        for field, value in content.items():
            setattr(variant, field, value)
            setattr(variant, f'{field}_ru', value)
        variant.save()

        for order, feat in enumerate(TESTING_FEATURES, start=1):
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

        for order, plan in enumerate(PRICING_PLANS, start=1):
            AdmissionPricingPlan.objects.update_or_create(
                variant=variant, order=order,
                defaults={
                    'highlight': plan['highlight'],
                    'badge_text': plan.get('badge_text', ''),
                    'badge_text_ru': plan.get('badge_text', ''),
                    'icon_svg': plan['icon_svg'],
                    'label': plan['label'],
                    'label_ru': plan['label'],
                    'price_value': plan['price_value'],
                    'price_currency': '₸',
                    'note': plan['note'],
                    'note_ru': plan['note'],
                },
            )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('admission', '0005_relabel_variant_leads'),
    ]
    operations = [
        migrations.RunPython(seed_all, noop),
    ]
