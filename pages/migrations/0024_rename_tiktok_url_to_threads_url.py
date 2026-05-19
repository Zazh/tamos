# Generated for tiktok_url → threads_url rename on 2026-05-19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0023_contactspage_facebook_url_contactspage_instagram_url_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='contactspage',
            old_name='tiktok_url',
            new_name='threads_url',
        ),
        migrations.AlterField(
            model_name='contactspage',
            name='threads_url',
            field=models.URLField(blank=True, max_length=300, verbose_name='Threads URL'),
        ),
    ]
