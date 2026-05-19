# Удаление соцсетей с ContactsPage — после переезда в FooterPage (0025).

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0025_create_footerpage'),
    ]

    operations = [
        migrations.RemoveField(model_name='contactspage', name='facebook_url'),
        migrations.RemoveField(model_name='contactspage', name='instagram_url'),
        migrations.RemoveField(model_name='contactspage', name='telegram_url'),
        migrations.RemoveField(model_name='contactspage', name='threads_url'),
    ]
