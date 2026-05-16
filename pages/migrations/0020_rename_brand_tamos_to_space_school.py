"""Data migration: переименование бренда «Tamos Space School» → «Space School»
в текстовых полях всех моделей проекта (2026-05-16).

Идемпотентно: REPLACE на строке без вхождения = no-op. Используется
django.db.models.functions.Replace на уровне SQL — не тянем строки в Python.

Покрывает translatable поля (modeltranslation создаёт _ru/_kk/_en колонки;
обновляем все три + базовое поле, чтобы избежать рассинхрона если активный
язык вдруг отличается от ru).
"""
from django.db import migrations
from django.db.models import F, Value
from django.db.models.functions import Replace


OLD = 'Tamos Space School'
NEW = 'Space School'

# Список (app_label, model_name, [field_names]) полей для обновления.
# Источник правды — `manage.py shell` поиск 2026-05-16: 20 затронутых полей.
# Базовые поля без суффикса включены: modeltranslation хранит их параллельно с
# _<lang> вариантами, и SET REPLACE обновит их одной транзакцией.
TARGETS = [
    ('pages', 'HomePage', [
        'seo_title', 'seo_title_ru', 'seo_title_kk', 'seo_title_en',
        'seo_description', 'seo_description_ru', 'seo_description_kk', 'seo_description_en',
        'og_title', 'og_title_ru', 'og_title_kk', 'og_title_en',
        'og_description', 'og_description_ru', 'og_description_kk', 'og_description_en',
    ]),
    ('admission', 'AdmissionVariant', [
        'hero_lead', 'hero_lead_ru', 'hero_lead_kk', 'hero_lead_en',
    ]),
    ('gallery', 'GalleryImage', [
        'alt', 'alt_ru', 'alt_kk', 'alt_en',
    ]),
]


def rename_brand(apps, schema_editor):
    for app_label, model_name, fields in TARGETS:
        Model = apps.get_model(app_label, model_name)
        for field in fields:
            updates = {field: Replace(F(field), Value(OLD), Value(NEW))}
            Model.objects.filter(**{f'{field}__contains': OLD}).update(**updates)


def reverse_rename(apps, schema_editor):
    """Обратное переименование. Не идеально (не различает оригинальный
    'Space School' и переименованный), но даёт возможность отката если что."""
    for app_label, model_name, fields in TARGETS:
        Model = apps.get_model(app_label, model_name)
        for field in fields:
            updates = {field: Replace(F(field), Value(NEW), Value(OLD))}
            Model.objects.filter(**{f'{field}__contains': NEW}).update(**updates)


class Migration(migrations.Migration):
    dependencies = [
        ('pages', '0019_contactspage_og_description_and_more'),
        ('admission', '0001_initial'),
        ('gallery', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(rename_brand, reverse_code=reverse_rename),
    ]
