"""Починка UI-лейблов AdmissionPage: русский текст в колонках `_kk`/`_en`.

Причина бага: у 8 translatable-полей в модели стоял `default='<русский текст>'`.
modeltranslation копирует `default` базового поля во ВСЕ сгенерированные
колонки (`_ru`/`_kk`/`_en`), поэтому казахская и английская версии страницы
поступления рождались уже заполненными по-русски. Раз колонка непустая —
fallback на `_ru` не срабатывал, а авто-перевод в backoffice считал поле
переведённым и не трогал его. Отсюда «блок не переключается».

`0014` убрала defaults из модели; здесь чиним уже созданные строки:
перезаписываем `_kk`/`_en` только там, где лежит ровно русский дефолт
(или пусто) — ручные переводы менеджеров не трогаем.
"""
from django.db import migrations


# base_field -> (русский дефолт, kk, en)
LABELS = {
    'breadcrumb_root_label': ('Поступление', 'Қабылдау', 'Admission'),
    'department_dropdown_label': ('Отделение:', 'Бөлім:', 'Department:'),
    'grade_dropdown_label': ('Классы:', 'Сыныптар:', 'Grades:'),
    'testing_price_label': ('Стоимость тестирования', 'Тестілеу құны', 'Testing fee'),
    'pricing_included_title': ('Стоимость включает', 'Құнына кіреді', 'Price includes'),
    'pricing_excluded_title': ('Не включено', 'Кірмейді', 'Not included'),
    'documents_title': (
        'Документы для зачисления',
        'Қабылдауға қажетті құжаттар',
        'Documents for enrolment',
    ),
    'consultation_cta_text': (
        'Записаться на консультацию',
        'Кеңеске жазылу',
        'Book a consultation',
    ),
}


def fix_labels(apps, schema_editor):
    AdmissionPage = apps.get_model('admission', 'AdmissionPage')
    for page in AdmissionPage.objects.all():
        changed = []
        for base, (ru_default, kk, en) in LABELS.items():
            # `_ru` мог остаться пустым (значение жило только в базовой колонке).
            if not getattr(page, f'{base}_ru', None):
                setattr(page, f'{base}_ru', getattr(page, base, None) or ru_default)
                changed.append(f'{base}_ru')
            for lang, value in (('kk', kk), ('en', en)):
                attr = f'{base}_{lang}'
                current = getattr(page, attr, None)
                # Перезаписываем только русский дефолт / пустоту.
                if not current or current == ru_default:
                    setattr(page, attr, value)
                    changed.append(attr)
        if changed:
            page.save(update_fields=changed)


def unfix_labels(apps, schema_editor):
    """Откат: возвращаем русский дефолт туда, где стоит наш перевод."""
    AdmissionPage = apps.get_model('admission', 'AdmissionPage')
    for page in AdmissionPage.objects.all():
        changed = []
        for base, (ru_default, kk, en) in LABELS.items():
            for lang, value in (('kk', kk), ('en', en)):
                attr = f'{base}_{lang}'
                if getattr(page, attr, None) == value:
                    setattr(page, attr, ru_default)
                    changed.append(attr)
        if changed:
            page.save(update_fields=changed)


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0014_alter_admissionpage_breadcrumb_root_label_and_more'),
    ]

    operations = [
        migrations.RunPython(fix_labels, unfix_labels),
    ]
