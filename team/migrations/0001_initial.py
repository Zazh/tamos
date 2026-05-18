import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('regions', '0005_seed_inactive_cities'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeamMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(help_text='Сегмент в URL: aigerim-nurlanova. Уникален в пределах региона.', max_length=200, verbose_name='Slug')),
                ('name', models.CharField(max_length=120, verbose_name='Имя')),
                ('name_ru', models.CharField(max_length=120, null=True, verbose_name='Имя')),
                ('name_kk', models.CharField(max_length=120, null=True, verbose_name='Имя')),
                ('name_en', models.CharField(max_length=120, null=True, verbose_name='Имя')),
                ('role', models.CharField(max_length=160, verbose_name='Должность')),
                ('role_ru', models.CharField(max_length=160, null=True, verbose_name='Должность')),
                ('role_kk', models.CharField(max_length=160, null=True, verbose_name='Должность')),
                ('role_en', models.CharField(max_length=160, null=True, verbose_name='Должность')),
                ('meta', models.CharField(blank=True, help_text='Напр. «PhD в педагогике · 20 лет в международном образовании».', max_length=240, verbose_name='Мета-строка')),
                ('meta_ru', models.CharField(blank=True, help_text='Напр. «PhD в педагогике · 20 лет в международном образовании».', max_length=240, null=True, verbose_name='Мета-строка')),
                ('meta_kk', models.CharField(blank=True, help_text='Напр. «PhD в педагогике · 20 лет в международном образовании».', max_length=240, null=True, verbose_name='Мета-строка')),
                ('meta_en', models.CharField(blank=True, help_text='Напр. «PhD в педагогике · 20 лет в международном образовании».', max_length=240, null=True, verbose_name='Мета-строка')),
                ('quote', models.TextField(blank=True, help_text='Опционально. На странице списка не выводится; показывается только на детальной.', verbose_name='Цитата')),
                ('quote_ru', models.TextField(blank=True, help_text='Опционально. На странице списка не выводится; показывается только на детальной.', null=True, verbose_name='Цитата')),
                ('quote_kk', models.TextField(blank=True, help_text='Опционально. На странице списка не выводится; показывается только на детальной.', null=True, verbose_name='Цитата')),
                ('quote_en', models.TextField(blank=True, help_text='Опционально. На странице списка не выводится; показывается только на детальной.', null=True, verbose_name='Цитата')),
                ('bio', models.TextField(blank=True, help_text='Развёрнутое описание для детальной страницы. HTML рендерится через |safe (h2/h3, p, ul/ol/li, blockquote).', verbose_name='Биография')),
                ('bio_ru', models.TextField(blank=True, help_text='Развёрнутое описание для детальной страницы. HTML рендерится через |safe (h2/h3, p, ul/ol/li, blockquote).', null=True, verbose_name='Биография')),
                ('bio_kk', models.TextField(blank=True, help_text='Развёрнутое описание для детальной страницы. HTML рендерится через |safe (h2/h3, p, ul/ol/li, blockquote).', null=True, verbose_name='Биография')),
                ('bio_en', models.TextField(blank=True, help_text='Развёрнутое описание для детальной страницы. HTML рендерится через |safe (h2/h3, p, ul/ol/li, blockquote).', null=True, verbose_name='Биография')),
                ('linkedin_url', models.URLField(blank=True, help_text='Полный URL профиля. Если указан — на детальной появится кнопка.', verbose_name='Ссылка на LinkedIn')),
                ('photo', models.ImageField(blank=True, null=True, upload_to='team/photos/', verbose_name='Фото')),
                ('order', models.PositiveSmallIntegerField(default=0, verbose_name='Порядок')),
                ('is_published', models.BooleanField(db_index=True, default=True, verbose_name='Опубликован')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создано')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Обновлено')),
                ('region', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='team_members', to='regions.region', verbose_name='Регион')),
            ],
            options={
                'verbose_name': 'Член команды',
                'verbose_name_plural': 'Команда',
                'ordering': ['order', 'pk'],
            },
        ),
        migrations.CreateModel(
            name='TeamResumeItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('period', models.CharField(blank=True, help_text='Напр. «2018–2022» или «2024». Не переводится.', max_length=80, verbose_name='Период')),
                ('title', models.CharField(help_text='Должность, степень, организация — одной строкой.', max_length=300, verbose_name='Описание')),
                ('title_ru', models.CharField(help_text='Должность, степень, организация — одной строкой.', max_length=300, null=True, verbose_name='Описание')),
                ('title_kk', models.CharField(help_text='Должность, степень, организация — одной строкой.', max_length=300, null=True, verbose_name='Описание')),
                ('title_en', models.CharField(help_text='Должность, степень, организация — одной строкой.', max_length=300, null=True, verbose_name='Описание')),
                ('order', models.PositiveSmallIntegerField(default=0, verbose_name='Порядок')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='resume_items', to='team.teammember', verbose_name='Член команды')),
            ],
            options={
                'verbose_name': 'Пункт резюме',
                'verbose_name_plural': 'Резюме',
                'ordering': ['order', 'pk'],
            },
        ),
        migrations.AddConstraint(
            model_name='teammember',
            constraint=models.UniqueConstraint(fields=('region', 'slug'), name='team_member_region_slug_unique'),
        ),
    ]
