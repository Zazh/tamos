"""
Подставляет в HomePage.hero_title (base + ru) HTML-разметку из прототипа
`spaceschool/pages/home.html`. Идемпотентно: апдейт по region.

После раскатки шаблон рендерит hero_title через |safe — менеджер может
дальше править разметку в админке (`hero-fit` / `hero-break` / `text-gold`).
"""
from django.db import migrations


HERO_TITLE_HTML = (
    '<span class="hero-fit">Лучшее образование </span>'
    '<span class="hero-fit"><span class="hero-break">для будущего вашего </span></span>'
    '<span class="hero-fit">ребёнка</span>'
)


def seed_hero_html(apps, schema_editor):
    HomePage = apps.get_model('pages', 'HomePage')
    HomePage.objects.update(
        hero_title=HERO_TITLE_HTML,
        hero_title_ru=HERO_TITLE_HTML,
    )


def unseed_hero_html(apps, schema_editor):
    # Без реверса — данные относятся к контенту, не к схеме. Пустой rollback,
    # чтобы migrate реально перешла, не упав на отсутствии reverse.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('pages', '0009_alter_homepage_hero_title_and_more'),
    ]
    operations = [
        migrations.RunPython(seed_hero_html, unseed_hero_html),
    ]
