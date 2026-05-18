"""Schema-часть глобализации BlogCategory/BlogTag.

- удаляем UniqueConstraint(region, slug),
- удаляем FK region,
- делаем slug сам по себе UNIQUE.

Data-смерж выполнен в 0006.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0006_drop_region_from_taxonomy'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='blogcategory',
            name='blog_category_region_slug_unique',
        ),
        migrations.RemoveConstraint(
            model_name='blogtag',
            name='blog_tag_region_slug_unique',
        ),
        migrations.RemoveField(
            model_name='blogcategory',
            name='region',
        ),
        migrations.RemoveField(
            model_name='blogtag',
            name='region',
        ),
        migrations.AlterField(
            model_name='blogcategory',
            name='slug',
            field=models.SlugField(
                'Slug',
                max_length=64,
                unique=True,
                help_text='Машинное имя категории (для ?category=...). Только латиница.',
            ),
        ),
        migrations.AlterField(
            model_name='blogtag',
            name='slug',
            field=models.SlugField(
                'Slug',
                max_length=64,
                unique=True,
            ),
        ),
    ]
