"""
Копирует декоративные фото (woman/library/kid/school-building) и фото
тимы из `static/` в `media/` через ImageField API. Идемпотентно:
пропускает поле, если оно уже заполнено.
"""
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.db import migrations


# (атрибут на ProgramPage, путь_в_static, имя_в_media)
PAGE_IMAGE_FIELDS = [
    ('audience_photo_woman',    'images/sections-images/woman.png',           'woman.png'),
    ('audience_photo_library',  'images/sections-images/library.jpg',         'library.jpg'),
    ('benefits_photo_kid',      'images/sections-images/kid.png',             'kid.png'),
    ('stats_photo',             'images/sections-images/school-building.jpg', 'school-building.jpg'),
]

TEAM_PHOTO = ('images/teams/1.jpg', 'team-placeholder.jpg')


def _static_path(rel: str) -> Path:
    return Path(settings.BASE_DIR) / 'static' / rel


def seed_program_assets(apps, schema_editor):
    ProgramPage = apps.get_model('programs', 'ProgramPage')
    ProgramTeamMember = apps.get_model('programs', 'ProgramTeamMember')

    for page in ProgramPage.objects.select_related('region').all():
        dirty = False
        for attr, src_rel, target_name in PAGE_IMAGE_FIELDS:
            field = getattr(page, attr)
            if field:
                continue  # уже наполнено — не перезаписываем
            src = _static_path(src_rel)
            if not src.exists():
                continue
            # Aktau получит суффикс к имени (FileField сам избежит коллизий через _<hash>).
            with open(src, 'rb') as f:
                field.save(target_name, File(f), save=False)
            dirty = True
        if dirty:
            page.save()

        for member in ProgramTeamMember.objects.filter(program_page=page):
            if member.photo:
                continue
            src = _static_path(TEAM_PHOTO[0])
            if not src.exists():
                continue
            with open(src, 'rb') as f:
                member.photo.save(TEAM_PHOTO[1], File(f), save=False)
            member.save()


def unseed_program_assets(apps, schema_editor):
    ProgramPage = apps.get_model('programs', 'ProgramPage')
    ProgramTeamMember = apps.get_model('programs', 'ProgramTeamMember')

    for page in ProgramPage.objects.all():
        for attr, _, _ in PAGE_IMAGE_FIELDS:
            field = getattr(page, attr)
            if field:
                field.delete(save=False)
        page.save()
    for member in ProgramTeamMember.objects.all():
        if member.photo:
            member.photo.delete(save=False)


class Migration(migrations.Migration):
    dependencies = [
        ('programs', '0002_seed_program_pages'),
    ]
    operations = [
        migrations.RunPython(seed_program_assets, unseed_program_assets),
    ]
