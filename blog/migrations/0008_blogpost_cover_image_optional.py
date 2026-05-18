"""cover_image теперь опциональный (blank=True) — позволяет сохранить
черновик без обложки. На сайте сработает плейсхолдер «Нет фото»."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0007_taxonomy_global_schema'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blogpost',
            name='cover_image',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='blog/covers/',
                verbose_name='Обложка',
                help_text='Опционально. Если не загружена — на сайте покажется плейсхолдер «Нет фото».',
            ),
        ),
    ]
