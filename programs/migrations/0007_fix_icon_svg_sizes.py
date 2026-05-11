"""
Добавляет CSS-класс размера к открывающему <svg ...> тегу в icon_svg.
Без класса SVG берёт дефолтный intrinsic-размер 300×150 (или схлопывается
в flex-контексте) — иконки на странице не появляются.

- ProgramAudienceItem: <svg class="h-9" ...>  — как в прототипе landing.html
  (родительский span — w-15 aspect-square, ~60×60; svg намеренно меньше).
- ProgramCertificateFeature: <svg class="block w-full h-full" ...>  —
  родительский span — w-8 h-8 (32×32), svg должен заполнить его целиком.

Идемпотентно: если в открывающем теге уже есть атрибут `class=` —
поле не трогается.
"""
from django.db import migrations


def _inject_class(svg_markup: str, css_class: str) -> str:
    """Вставить `class="..."` в первый <svg ...> тег. Без regex — простой split."""
    if not svg_markup or not svg_markup.startswith('<svg '):
        return svg_markup
    head, sep, tail = svg_markup.partition('>')
    if not sep:
        return svg_markup
    if 'class=' in head:
        return svg_markup  # уже есть class — не трогаем
    return f'{head} class="{css_class}"{sep}{tail}'


def fix_icons(apps, schema_editor):
    Audience = apps.get_model('programs', 'ProgramAudienceItem')
    Cert = apps.get_model('programs', 'ProgramCertificateFeature')

    for item in Audience.objects.exclude(icon_svg=''):
        new = _inject_class(item.icon_svg, 'h-9')
        if new != item.icon_svg:
            item.icon_svg = new
            item.save(update_fields=['icon_svg'])

    for item in Cert.objects.exclude(icon_svg=''):
        new = _inject_class(item.icon_svg, 'block w-full h-full')
        if new != item.icon_svg:
            item.icon_svg = new
            item.save(update_fields=['icon_svg'])


def noop(apps, schema_editor):
    # Без реверса — только контент.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('programs', '0006_seed_program_hero_html'),
    ]
    operations = [
        migrations.RunPython(fix_icons, noop),
    ]
