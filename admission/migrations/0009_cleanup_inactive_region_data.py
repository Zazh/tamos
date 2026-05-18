"""Удалить mock-данные AdmissionPage для inactive регионов (almaty/shymkent).

Изначально seed-миграции 0003_seed_admission_pages и 0006_seed_all_variants
заполняли placeholder-контент для ВСЕХ регионов в БД, включая inactive
(almaty, shymkent). Менеджер просил очистить эти mock'и: реальные данные есть
только для активных регионов (astana, aktau).

Удаление AdmissionPage → каскадом снесёт всё связанное:
  - AdmissionVariant (6 на регион)
  - AdmissionTestingFeature (4×6 = 24)
  - AdmissionPricingPlan (3×6 = 18)
  - AdmissionIncludedItem (4)
  - AdmissionDocument (6)

Идемпотентно: если страниц для inactive-регионов нет — ничего не делаем.

Reverse — no-op: восстановить placeholder'ы из этой миграции мы не пытаемся
(их легко пересоздать через 0003/0006 если регион снова станет активным).
"""

from django.db import migrations


def cleanup_inactive(apps, schema_editor):
    AdmissionPage = apps.get_model('admission', 'AdmissionPage')
    AdmissionPage.objects.filter(region__is_active=False).delete()


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0008_admissionvariant_og_description_and_more'),
        ('regions', '0005_seed_inactive_cities'),
    ]

    operations = [
        migrations.RunPython(cleanup_inactive, noop_reverse),
    ]
