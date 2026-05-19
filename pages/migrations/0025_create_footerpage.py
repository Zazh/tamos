# Создание FooterPage + перенос соцсетей и стартового текста с ContactsPage.
#
# До этой миграции футер использовал захардкоженный текст через {% trans %}
# и брал соцсети из ContactsPage. После — управление переносится в отдельную
# модель/раздел backoffice.

import django.db.models.deletion
from django.db import migrations, models


DEFAULT_INTRO_TEXT_RU = (
    'Space School — международная школа нового поколения, где дети учатся '
    'думать глобально, готовятся к поступлению в ведущие университеты мира '
    'и получают двойной сертификат с правом сдачи SAT.'
)


def seed_footer_pages(apps, schema_editor):
    Region = apps.get_model('regions', 'Region')
    ContactsPage = apps.get_model('pages', 'ContactsPage')
    FooterPage = apps.get_model('pages', 'FooterPage')

    for region in Region.objects.all():
        contacts = ContactsPage.objects.filter(region=region).first()
        FooterPage.objects.get_or_create(
            region=region,
            defaults={
                'intro_text': DEFAULT_INTRO_TEXT_RU,
                'intro_text_ru': DEFAULT_INTRO_TEXT_RU,
                'facebook_url': contacts.facebook_url if contacts else '',
                'instagram_url': contacts.instagram_url if contacts else '',
                'threads_url': contacts.threads_url if contacts else '',
                'telegram_url': contacts.telegram_url if contacts else '',
            },
        )


def noop_reverse(apps, schema_editor):
    """На откате просто удалим все записи (схему откатит RemoveField)."""
    FooterPage = apps.get_model('pages', 'FooterPage')
    FooterPage.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0024_rename_tiktok_url_to_threads_url'),
        ('regions', '0005_seed_inactive_cities'),
    ]

    operations = [
        migrations.CreateModel(
            name='FooterPage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('intro_text', models.TextField(blank=True, help_text='Короткий параграф под логотипом школы в футере. Если пусто — параграф скрыт.', verbose_name='Текст под лого')),
                ('intro_text_ru', models.TextField(blank=True, help_text='Короткий параграф под логотипом школы в футере. Если пусто — параграф скрыт.', null=True, verbose_name='Текст под лого')),
                ('intro_text_kk', models.TextField(blank=True, help_text='Короткий параграф под логотипом школы в футере. Если пусто — параграф скрыт.', null=True, verbose_name='Текст под лого')),
                ('intro_text_en', models.TextField(blank=True, help_text='Короткий параграф под логотипом школы в футере. Если пусто — параграф скрыт.', null=True, verbose_name='Текст под лого')),
                ('facebook_url', models.URLField(blank=True, max_length=300, verbose_name='Facebook URL')),
                ('instagram_url', models.URLField(blank=True, max_length=300, verbose_name='Instagram URL')),
                ('threads_url', models.URLField(blank=True, max_length=300, verbose_name='Threads URL')),
                ('telegram_url', models.URLField(blank=True, max_length=300, verbose_name='Telegram URL')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Обновлено')),
                ('region', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='footer_page', to='regions.region', verbose_name='Регион')),
            ],
            options={
                'verbose_name': 'Страница «Футер»',
                'verbose_name_plural': 'Страницы «Футер»',
            },
        ),
        migrations.RunPython(seed_footer_pages, noop_reverse),
    ]
