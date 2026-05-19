"""
Чинит карточку «Хочет большего, чем обычная школа» в Астане: при ручной
правке через бэкофис у неё пропали `icon_svg` и `description_ru` (вместо
текста — «Восстановлено»). Копируем эти два поля из той же карточки в
Актау, где они корректные.

Идемпотентно: запускается только если у Астана-карточки icon_svg пустой
или description_ru == 'Восстановлено'.
"""
from django.db import migrations


TARGET_TITLE_RU = 'Хочет большего, чем обычная школа'


def fix_card(apps, schema_editor):
    Audience = apps.get_model('programs', 'ProgramAudienceItem')

    aktau = (
        Audience.objects
        .filter(program_page__region__slug='aktau', title_ru=TARGET_TITLE_RU)
        .first()
    )
    if aktau is None or not aktau.icon_svg:
        return

    for astana in Audience.objects.filter(
        program_page__region__slug='astana', title_ru=TARGET_TITLE_RU
    ):
        changed = False
        if not astana.icon_svg:
            astana.icon_svg = aktau.icon_svg
            changed = True
        if (astana.description_ru or '').strip() in ('', 'Восстановлено'):
            astana.description_ru = aktau.description_ru
            changed = True
        if changed:
            astana.save(update_fields=['icon_svg', 'description_ru'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('programs', '0012_delete_programteammember'),
    ]
    operations = [
        migrations.RunPython(fix_card, noop),
    ]
