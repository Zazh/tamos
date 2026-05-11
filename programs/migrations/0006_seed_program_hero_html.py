"""
Подставляет в ProgramPage.hero_title (base + ru) HTML-разметку из прототипа
`spaceschool/pages/landing.html`. Идемпотентно: апдейт по region.

В прототипе акцент «TOP-100» подсвечен жёлтым через <span class="text-gold">,
средняя строка обёрнута в <span class="hero-break"> для аккуратного
переноса на десктопе.
"""
from django.db import migrations


HERO_TITLE_HTML = (
    '<span class="hero-fit">Школа для детей</span>'
    '<span class="hero-fit">которые <span class="hero-break">поступят</span></span>'
    '<span class="hero-fit">в <span class="text-gold">TOP-100</span> вузов</span>'
)


def seed_hero_html(apps, schema_editor):
    ProgramPage = apps.get_model('programs', 'ProgramPage')
    ProgramPage.objects.update(
        hero_title=HERO_TITLE_HTML,
        hero_title_ru=HERO_TITLE_HTML,
    )


def unseed_hero_html(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('programs', '0005_alter_programpage_hero_title_and_more'),
    ]
    operations = [
        migrations.RunPython(seed_hero_html, unseed_hero_html),
    ]
