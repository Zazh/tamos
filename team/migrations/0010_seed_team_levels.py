"""Проставляет уровни преподавания + флаг администрации существующим
членам команды (соответствует прежней привязке к admission.GradeGroup
из 0005_seed_team_grade_groups, но в новой 3-уровневой модели).

Маппинг приблизительный — менеджер донастроит вручную через backoffice.
"""
from django.db import migrations


# slug → (teaches_primary, teaches_middle, teaches_senior, is_admin)
ASSIGNMENTS = {
    # ----- Astana -----
    'aigerim-nurlanova':  (False, False, False, True),   # директор
    'daniyar-zholdas':    (False, True,  True,  True),   # академ. директор + ведёт математику в 5-8/9-11
    'aliya-bekova':       (False, False, False, True),   # куратор Cambridge
    'arman-toleukhanov':  (False, False, True,  False),  # инженер JAXA → старшие
    'madina-aibekova':    (False, False, True,  False),  # физмат → старшие
    # ----- Aktau -----
    'erlan-mukhanov':     (False, False, False, True),   # директор
    'gulnara-ospanova':   (False, False, False, True),   # координатор
    'timur-aitkali':      (False, True,  True,  False),  # математика 5-11
    'aigul-saparova':     (True,  True,  False, False),  # английский младшим+средним
    'nurlan-ergaliev':    (False, True,  False, False),  # робототехника средним
}


def seed(apps, schema_editor):
    TeamMember = apps.get_model('team', 'TeamMember')
    for slug, (primary, middle, senior, admin) in ASSIGNMENTS.items():
        TeamMember.objects.filter(slug=slug).update(
            teaches_primary=primary,
            teaches_middle=middle,
            teaches_senior=senior,
            is_admin=admin,
        )


def unseed(apps, schema_editor):
    TeamMember = apps.get_model('team', 'TeamMember')
    TeamMember.objects.filter(slug__in=ASSIGNMENTS.keys()).update(
        teaches_primary=False,
        teaches_middle=False,
        teaches_senior=False,
        is_admin=False,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('team', '0009_teammember_levels'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
