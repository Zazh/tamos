"""Помечает первых N членов команды как `is_featured` — они появляются на
лендинге «Программа» текущего региона (см. programs.views.ProgramView).

Идемпотентно: явный список slug'ов на регион. Если slug не существует,
запись пропускается тихо.
"""
from django.db import migrations


FEATURED_SLUGS = {
    'astana': [
        'aigerim-nurlanova',     # директор
        'daniyar-zholdas',       # академ. директор
        'arman-toleukhanov',     # инженер JAXA
        'madina-aibekova',       # тренер физмат-сборной
    ],
    'aktau': [
        'erlan-mukhanov',        # директор
        'gulnara-ospanova',      # академ. координатор
        'timur-aitkali',         # математика
        'nurlan-ergaliev',       # робототехника
    ],
}


def seed(apps, schema_editor):
    TeamMember = apps.get_model('team', 'TeamMember')
    for region_slug, member_slugs in FEATURED_SLUGS.items():
        TeamMember.objects.filter(
            region__slug=region_slug,
            slug__in=member_slugs,
        ).update(is_featured=True)


def unseed(apps, schema_editor):
    TeamMember = apps.get_model('team', 'TeamMember')
    all_slugs = [s for slugs in FEATURED_SLUGS.values() for s in slugs]
    TeamMember.objects.filter(slug__in=all_slugs).update(is_featured=False)


class Migration(migrations.Migration):

    dependencies = [
        ('team', '0007_teammember_is_featured'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
