# Generated for app `gallery` — initial schema.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('regions', '0005_seed_inactive_cities'),
    ]

    operations = [
        migrations.CreateModel(
            name='GalleryCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(help_text='Машинное имя категории (для ?category=...). Только латиница.', max_length=64, unique=True, verbose_name='Slug')),
                ('name', models.CharField(max_length=80, verbose_name='Название')),
                ('name_ru', models.CharField(max_length=80, null=True, verbose_name='Название')),
                ('name_kk', models.CharField(max_length=80, null=True, verbose_name='Название')),
                ('name_en', models.CharField(max_length=80, null=True, verbose_name='Название')),
                ('order', models.PositiveSmallIntegerField(default=0, verbose_name='Порядок')),
                ('is_published', models.BooleanField(db_index=True, default=True, verbose_name='Опубликовано')),
            ],
            options={
                'verbose_name': 'Категория фотогалереи',
                'verbose_name_plural': 'Категории фотогалереи',
                'ordering': ['order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='GalleryImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(help_text='Обязательное поле в админке. Записи без файла в выдачу не попадают.', null=True, upload_to='gallery/', verbose_name='Изображение')),
                ('alt', models.CharField(blank=True, help_text='Для SEO/доступности. Если пусто — подставляется caption или slug категории.', max_length=300, verbose_name='Alt-текст')),
                ('alt_ru', models.CharField(blank=True, help_text='Для SEO/доступности. Если пусто — подставляется caption или slug категории.', max_length=300, null=True, verbose_name='Alt-текст')),
                ('alt_kk', models.CharField(blank=True, help_text='Для SEO/доступности. Если пусто — подставляется caption или slug категории.', max_length=300, null=True, verbose_name='Alt-текст')),
                ('alt_en', models.CharField(blank=True, help_text='Для SEO/доступности. Если пусто — подставляется caption или slug категории.', max_length=300, null=True, verbose_name='Alt-текст')),
                ('caption', models.CharField(blank=True, max_length=300, verbose_name='Подпись')),
                ('caption_ru', models.CharField(blank=True, max_length=300, null=True, verbose_name='Подпись')),
                ('caption_kk', models.CharField(blank=True, max_length=300, null=True, verbose_name='Подпись')),
                ('caption_en', models.CharField(blank=True, max_length=300, null=True, verbose_name='Подпись')),
                ('is_wide', models.BooleanField(default=False, help_text='Растягивает карточку на 2 колонки в мозаике (mosaic-card-wide).', verbose_name='Широкая карточка')),
                ('order', models.PositiveSmallIntegerField(default=0, help_text='Чем меньше — тем выше. При равных — по дате (свежие выше).', verbose_name='Порядок')),
                ('is_published', models.BooleanField(db_index=True, default=True, verbose_name='Опубликовано')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создано')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Обновлено')),
                ('category', models.ForeignKey(blank=True, help_text='Опционально. Влияет только на chip-фильтр на странице.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='images', to='gallery.gallerycategory', verbose_name='Категория')),
                ('region', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='gallery_images', to='regions.region', verbose_name='Регион')),
            ],
            options={
                'verbose_name': 'Фото в галерее',
                'verbose_name_plural': 'Фото в галерее',
                'ordering': ['order', '-created_at', '-pk'],
            },
        ),
    ]
