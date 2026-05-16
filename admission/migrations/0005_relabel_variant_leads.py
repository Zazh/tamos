"""Чинит hero_lead и pricing_lead у grade-1 вариантов: убирает дублирование
«отделение» (теперь оно входит в Department.name). Эти поля попали в БД
из предыдущей версии 0003_seed, где склейка с «отделение» делалась в Python.
Только grade-1, ru и kk — у остальных контент пустой."""
from django.db import migrations


DEPT_LABEL_RU = {
    'ru': 'русское отделение',
    'kz': 'казахское отделение',
}

GRADE_LABEL_RU = {
    '1': '1 класс',
}


def fix_leads(apps, schema_editor):
    AdmissionVariant = apps.get_model('admission', 'AdmissionVariant')
    for variant in AdmissionVariant.objects.select_related('department', 'grade'):
        if variant.grade.slug != '1':
            continue
        dept = DEPT_LABEL_RU.get(variant.department.slug)
        grade = GRADE_LABEL_RU.get(variant.grade.slug)
        if not dept or not grade:
            continue

        hero_lead = (
            f'Условия и этапы поступления в {dept}, {grade}, '
            f'в частную международную школу Space School по программе Cambridge Primary.'
        )
        pricing_lead = (
            f'Стоимость обучения для {grade} ({dept}) на 2026–2027 учебный год. '
            f'После выбора тарифа — подписание договора с менеджером.'
        )

        variant.hero_lead = hero_lead
        variant.hero_lead_ru = hero_lead
        variant.pricing_lead = pricing_lead
        variant.pricing_lead_ru = pricing_lead
        variant.save(update_fields=['hero_lead', 'hero_lead_ru', 'pricing_lead', 'pricing_lead_ru'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('admission', '0004_relabel_departments'),
    ]
    operations = [
        migrations.RunPython(fix_leads, noop),
    ]
