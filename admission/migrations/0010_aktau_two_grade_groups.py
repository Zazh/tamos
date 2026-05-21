"""В Актау оставить только 2 группы классов: «1 класс» и «2–4 класс».

Создаёт глобальную GradeGroup `2-4` (если нет), затем для региона
`aktau` пересобирает варианты: оставляет (dept × {1, 2-4}) и удаляет
лишние (2-7 / 2-6 / 8-11 / 7-11). Контент новых вариантов копируется из
seed-данных (build_variant_content + TESTING_FEATURES + PRICING_PLANS).

В Астане ничего не меняется — там продолжают использоваться 5
существующих групп. Новая GradeGroup `2-4` просто не имеет вариантов в
Астане, поэтому в её dropdown'е не появится (см. admission.views.
AdmissionView.available_grades).

Идемпотентно: повторный прогон не создаёт дубликатов и не удаляет
повторно (filter по slug-набору).
"""
from django.db import migrations

from admission.seed_data import PRICING_PLANS, TESTING_FEATURES, build_variant_content


NEW_GRADE = {
    'slug': '2-4',
    'order': 15,  # между 1 (order=10) и 2-7 (order=20)
    'name_ru': '2–4 класс',
    'name_kk': '2–4 сынып',
    'name_en': 'Grades 2–4',
    'short_name_ru': '2–4 кл.',
    'short_name_kk': '2–4 сын.',
    'short_name_en': 'G2–4',
}

OBSOLETE_AKTAU_GRADE_SLUGS = ['2-7', '2-6', '8-11', '7-11']


def _seed_variant_inlines(variant, AdmissionTestingFeature, AdmissionPricingPlan):
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


def forwards(apps, schema_editor):
    GradeGroup = apps.get_model('admission', 'GradeGroup')
    Department = apps.get_model('admission', 'Department')
    AdmissionPage = apps.get_model('admission', 'AdmissionPage')
    AdmissionVariant = apps.get_model('admission', 'AdmissionVariant')
    AdmissionTestingFeature = apps.get_model('admission', 'AdmissionTestingFeature')
    AdmissionPricingPlan = apps.get_model('admission', 'AdmissionPricingPlan')

    grade_2_4, _ = GradeGroup.objects.update_or_create(
        slug=NEW_GRADE['slug'],
        defaults={
            'order': NEW_GRADE['order'],
            'name': NEW_GRADE['name_ru'],
            'name_ru': NEW_GRADE['name_ru'],
            'name_kk': NEW_GRADE['name_kk'],
            'name_en': NEW_GRADE['name_en'],
            'short_name': NEW_GRADE['short_name_ru'],
            'short_name_ru': NEW_GRADE['short_name_ru'],
            'short_name_kk': NEW_GRADE['short_name_kk'],
            'short_name_en': NEW_GRADE['short_name_en'],
        },
    )

    try:
        aktau_page = AdmissionPage.objects.get(region__slug='aktau')
    except AdmissionPage.DoesNotExist:
        return

    # Создаём новые варианты (dept × 2-4)
    for dept in Department.objects.all():
        content = build_variant_content(dept.slug, NEW_GRADE['slug'])
        variant, _ = AdmissionVariant.objects.update_or_create(
            page=aktau_page,
            department=dept,
            grade=grade_2_4,
            defaults={
                'h1': content['h1'],
                'h1_ru': content['h1'],
                'hero_lead': content['hero_lead'],
                'hero_lead_ru': content['hero_lead'],
                'testing_lead': content['testing_lead'],
                'testing_lead_ru': content['testing_lead'],
                'result_intro': content['result_intro'],
                'result_intro_ru': content['result_intro'],
                'result_detail': content['result_detail'],
                'result_detail_ru': content['result_detail'],
                'pricing_lead': content['pricing_lead'],
                'pricing_lead_ru': content['pricing_lead'],
            },
        )
        _seed_variant_inlines(variant, AdmissionTestingFeature, AdmissionPricingPlan)

    # Удаляем лишние варианты в Актау
    AdmissionVariant.objects.filter(
        page=aktau_page,
        grade__slug__in=OBSOLETE_AKTAU_GRADE_SLUGS,
    ).delete()


def backwards(apps, schema_editor):
    AdmissionVariant = apps.get_model('admission', 'AdmissionVariant')
    AdmissionVariant.objects.filter(
        page__region__slug='aktau',
        grade__slug=NEW_GRADE['slug'],
    ).delete()
    # GradeGroup `2-4` оставляем — может использоваться вне Актау.


class Migration(migrations.Migration):
    dependencies = [
        ('admission', '0009_cleanup_inactive_region_data'),
    ]
    operations = [
        migrations.RunPython(forwards, backwards),
    ]
