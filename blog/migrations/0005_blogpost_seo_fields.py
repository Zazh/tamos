from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0004_bloggallery_bloggalleryimage_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='blogpost',
            name='seo_title',
            field=models.CharField(blank=True, help_text='50–60 символов. Если пусто — fallback на title.', max_length=80, verbose_name='SEO title (<title>)'),
        ),
        migrations.AddField(
            model_name='blogpost',
            name='seo_title_ru',
            field=models.CharField(blank=True, help_text='50–60 символов. Если пусто — fallback на title.', max_length=80, null=True, verbose_name='SEO title (<title>)'),
        ),
        migrations.AddField(
            model_name='blogpost',
            name='seo_title_kk',
            field=models.CharField(blank=True, help_text='50–60 символов. Если пусто — fallback на title.', max_length=80, null=True, verbose_name='SEO title (<title>)'),
        ),
        migrations.AddField(
            model_name='blogpost',
            name='seo_title_en',
            field=models.CharField(blank=True, help_text='50–60 символов. Если пусто — fallback на title.', max_length=80, null=True, verbose_name='SEO title (<title>)'),
        ),
        migrations.AddField(
            model_name='blogpost',
            name='seo_description',
            field=models.CharField(blank=True, help_text='150–160 символов. Если пусто — fallback на lead.', max_length=200, verbose_name='SEO description (meta)'),
        ),
        migrations.AddField(
            model_name='blogpost',
            name='seo_description_ru',
            field=models.CharField(blank=True, help_text='150–160 символов. Если пусто — fallback на lead.', max_length=200, null=True, verbose_name='SEO description (meta)'),
        ),
        migrations.AddField(
            model_name='blogpost',
            name='seo_description_kk',
            field=models.CharField(blank=True, help_text='150–160 символов. Если пусто — fallback на lead.', max_length=200, null=True, verbose_name='SEO description (meta)'),
        ),
        migrations.AddField(
            model_name='blogpost',
            name='seo_description_en',
            field=models.CharField(blank=True, help_text='150–160 символов. Если пусто — fallback на lead.', max_length=200, null=True, verbose_name='SEO description (meta)'),
        ),
        migrations.AddField(
            model_name='blogpost',
            name='og_title',
            field=models.CharField(blank=True, help_text='Если пусто — fallback на seo_title → title.', max_length=80, verbose_name='OG title'),
        ),
        migrations.AddField(
            model_name='blogpost',
            name='og_title_ru',
            field=models.CharField(blank=True, help_text='Если пусто — fallback на seo_title → title.', max_length=80, null=True, verbose_name='OG title'),
        ),
        migrations.AddField(
            model_name='blogpost',
            name='og_title_kk',
            field=models.CharField(blank=True, help_text='Если пусто — fallback на seo_title → title.', max_length=80, null=True, verbose_name='OG title'),
        ),
        migrations.AddField(
            model_name='blogpost',
            name='og_title_en',
            field=models.CharField(blank=True, help_text='Если пусто — fallback на seo_title → title.', max_length=80, null=True, verbose_name='OG title'),
        ),
        migrations.AddField(
            model_name='blogpost',
            name='og_description',
            field=models.CharField(blank=True, help_text='Если пусто — fallback на seo_description → lead.', max_length=300, verbose_name='OG description'),
        ),
        migrations.AddField(
            model_name='blogpost',
            name='og_description_ru',
            field=models.CharField(blank=True, help_text='Если пусто — fallback на seo_description → lead.', max_length=300, null=True, verbose_name='OG description'),
        ),
        migrations.AddField(
            model_name='blogpost',
            name='og_description_kk',
            field=models.CharField(blank=True, help_text='Если пусто — fallback на seo_description → lead.', max_length=300, null=True, verbose_name='OG description'),
        ),
        migrations.AddField(
            model_name='blogpost',
            name='og_description_en',
            field=models.CharField(blank=True, help_text='Если пусто — fallback на seo_description → lead.', max_length=300, null=True, verbose_name='OG description'),
        ),
        migrations.AddField(
            model_name='blogpost',
            name='og_image',
            field=models.ImageField(blank=True, help_text='1200×630 для соцсетей. Если пусто — fallback на обложку поста.', null=True, upload_to='blog/og/', verbose_name='OG/share картинка'),
        ),
    ]
