"""Заголовок списка способов оплаты — короткий h4 в стиле «Стоимость включает».

Было (0017): фраза «Оплату можно совершать тремя удобными для вас способами:»
абзацем над списком. Стало: «Три удобных способа оплаты» как h4 (шаблон
detail.html переведён на тот же markup, что у «Стоимость включает»).
Заменяем только точное старое значение — ручные правки менеджеров не трогаем.
AlterField — обновлённый help_text. Reverse возвращает старую фразу.
"""
from django.db import migrations, models


TITLE_OLD = {
    'ru': 'Оплату можно совершать тремя удобными для вас способами:',
    'kk': 'Төлемді сізге ыңғайлы үш тәсілмен жасауға болады:',
    'en': 'Payment can be made in three convenient ways:',
}
TITLE_NEW = {
    'ru': 'Три удобных способа оплаты',
    'kk': 'Төлемнің үш ыңғайлы тәсілі',
    'en': 'Three convenient payment options',
}


def _swap(apps, mapping_from, mapping_to):
    AdmissionPage = apps.get_model('admission', 'AdmissionPage')
    for page in AdmissionPage.objects.all():
        changed = []
        for lang, old in mapping_from.items():
            attr = f'payment_methods_title_{lang}'
            if (getattr(page, attr, None) or '').strip() == old:
                setattr(page, attr, mapping_to[lang])
                changed.append(attr)
                if lang == 'ru':
                    page.payment_methods_title = mapping_to[lang]
                    changed.append('payment_methods_title')
        if changed:
            page.save(update_fields=changed)


def forwards(apps, schema_editor):
    _swap(apps, TITLE_OLD, TITLE_NEW)


def backwards(apps, schema_editor):
    _swap(apps, TITLE_NEW, TITLE_OLD)


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0018_pricing_single_card_any_deadline'),
    ]

    operations = [
        migrations.AlterField(
            model_name='admissionpage',
            name='payment_methods_title',
            field=models.CharField(blank=True, help_text='Заголовок h4 над нумерованным списком способов оплаты (под прайс-картой и текстом про взнос), в стиле «Стоимость включает». Напр. «Три удобных способа оплаты». Пусто — список без заголовка.', max_length=200, verbose_name='Заголовок списка «Способы оплаты»'),
        ),
        migrations.AlterField(
            model_name='admissionpage',
            name='payment_methods_title_en',
            field=models.CharField(blank=True, help_text='Заголовок h4 над нумерованным списком способов оплаты (под прайс-картой и текстом про взнос), в стиле «Стоимость включает». Напр. «Три удобных способа оплаты». Пусто — список без заголовка.', max_length=200, null=True, verbose_name='Заголовок списка «Способы оплаты»'),
        ),
        migrations.AlterField(
            model_name='admissionpage',
            name='payment_methods_title_kk',
            field=models.CharField(blank=True, help_text='Заголовок h4 над нумерованным списком способов оплаты (под прайс-картой и текстом про взнос), в стиле «Стоимость включает». Напр. «Три удобных способа оплаты». Пусто — список без заголовка.', max_length=200, null=True, verbose_name='Заголовок списка «Способы оплаты»'),
        ),
        migrations.AlterField(
            model_name='admissionpage',
            name='payment_methods_title_ru',
            field=models.CharField(blank=True, help_text='Заголовок h4 над нумерованным списком способов оплаты (под прайс-картой и текстом про взнос), в стиле «Стоимость включает». Напр. «Три удобных способа оплаты». Пусто — список без заголовка.', max_length=200, null=True, verbose_name='Заголовок списка «Способы оплаты»'),
        ),
        migrations.RunPython(forwards, backwards),
    ]
