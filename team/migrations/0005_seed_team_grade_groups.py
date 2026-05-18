"""Привязывает существующих учителей к группам классов admission.GradeGroup.

Идемпотентно: каждая привязка идёт через .set(...), безопасно при повторе.
Директор / академ. координатор / куратор Cambridge остаются БЕЗ grade_groups —
они администрация, отображаются на «Все».
"""
from django.db import migrations


# slug TeamMember → список slug'ов admission.GradeGroup
# Используем «русские» границы: 1, 2-7, 8-11 (см. admission/0002_seed_lookups).
# Тренеры/наставники по физмату — обычно средние и старшие классы.
ASTANA_BINDINGS = {
    # Айгерим — директор, без grade
    # Алия — куратор Cambridge International, без grade (междисциплинарно)
    'daniyar-zholdas': ['2-7', '8-11'],          # академ. директор + ведёт математику
    'arman-toleukhanov': ['8-11'],               # инженер JAXA → старшие
    'madina-aibekova': ['8-11'],                 # тренер физмат-сборной → старшие
}

AKTAU_BINDINGS = {
    # Ерлан — директор, без grade
    # Гульнара — академ. координатор, без grade
    'timur-aitkali': ['2-7', '8-11'],            # математика
    'aigul-saparova': ['1', '2-7'],              # английский младшим
    'nurlan-ergaliev': ['2-7'],                  # робототехника средним
}


def _bind(apps, slug_to_grades):
    TeamMember = apps.get_model('team', 'TeamMember')
    GradeGroup = apps.get_model('admission', 'GradeGroup')

    grades_by_slug = {g.slug: g for g in GradeGroup.objects.all()}

    for member_slug, grade_slugs in slug_to_grades.items():
        member = TeamMember.objects.filter(slug=member_slug).first()
        if member is None:
            continue
        wanted = [grades_by_slug[s] for s in grade_slugs if s in grades_by_slug]
        member.grade_groups.set(wanted)


def seed(apps, schema_editor):
    _bind(apps, ASTANA_BINDINGS)
    _bind(apps, AKTAU_BINDINGS)


def unseed(apps, schema_editor):
    TeamMember = apps.get_model('team', 'TeamMember')
    all_slugs = list(ASTANA_BINDINGS.keys()) + list(AKTAU_BINDINGS.keys())
    for slug in all_slugs:
        member = TeamMember.objects.filter(slug=slug).first()
        if member is not None:
            member.grade_groups.clear()


class Migration(migrations.Migration):

    dependencies = [
        ('team', '0004_teammember_grade_groups'),
        ('admission', '0002_seed_lookups'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
