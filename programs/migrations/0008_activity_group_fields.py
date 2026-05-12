# Generated for activity group/details fields (program landing).

from django.db import migrations, models


CHAR_FIELDS = [
    # (name, max_length, verbose_name, help_text)
    ('class_range', 60, 'Классы', 'Подзаголовок в шапке (напр. «1–5 класс»).'),
    ('group_title', 120, 'Название группы', 'Заголовок карточки-группы (напр. «Основная группа» или «1–5 класс»).'),
    ('schedule', 120, 'Расписание', 'Напр. «Пн, Ср · 14:00–15:30».'),
    ('students_text', 80, 'Учащихся (текст)', 'Напр. «От 5 учеников» или «До 10 учеников».'),
    ('location', 120, 'Локация', ''),
    ('price', 60, 'Стоимость', 'Напр. «25 000 ₸/мес».'),
    ('trainer_name', 200, 'ФИО тренера', ''),
]

LOCALES = ('ru', 'kk', 'en')


def _make_char_ops():
    ops = []
    for name, max_length, vname, htext in CHAR_FIELDS:
        kwargs = dict(blank=True, max_length=max_length, verbose_name=vname)
        if htext:
            kwargs['help_text'] = htext
        ops.append(migrations.AddField(
            model_name='programactivityitem', name=name,
            field=models.CharField(**kwargs),
        ))
        for code in LOCALES:
            ops.append(migrations.AddField(
                model_name='programactivityitem', name=f'{name}_{code}',
                field=models.CharField(null=True, **kwargs),
            ))
    return ops


def _make_text_ops():
    ops = []
    kwargs = dict(blank=True, verbose_name='Био тренера')
    ops.append(migrations.AddField(
        model_name='programactivityitem', name='trainer_bio',
        field=models.TextField(**kwargs),
    ))
    for code in LOCALES:
        ops.append(migrations.AddField(
            model_name='programactivityitem', name=f'trainer_bio_{code}',
            field=models.TextField(null=True, **kwargs),
        ))
    return ops


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0007_fix_icon_svg_sizes'),
    ]

    operations = [
        # time_label теперь устаревшее — расписание переехало в schedule.
        migrations.AlterField(
            model_name='programactivityitem',
            name='time_label',
            field=models.CharField(
                blank=True, max_length=60,
                verbose_name='Время (устаревшее, не используется)',
                help_text='Старое поле, оставлено для совместимости. Расписание теперь в «schedule».',
            ),
        ),
        *[
            migrations.AlterField(
                model_name='programactivityitem',
                name=f'time_label_{code}',
                field=models.CharField(
                    blank=True, null=True, max_length=60,
                    verbose_name='Время (устаревшее, не используется)',
                    help_text='Старое поле, оставлено для совместимости. Расписание теперь в «schedule».',
                ),
            )
            for code in LOCALES
        ],
        # description — уточнили verbose_name (раньше было «открывается в аккордеоне»).
        migrations.AlterField(
            model_name='programactivityitem',
            name='description',
            field=models.TextField(blank=True, verbose_name='Описание (вверху раскрытого блока)'),
        ),
        *[
            migrations.AlterField(
                model_name='programactivityitem',
                name=f'description_{code}',
                field=models.TextField(blank=True, null=True, verbose_name='Описание (вверху раскрытого блока)'),
            )
            for code in LOCALES
        ],
        # category — уточнили help_text.
        migrations.AlterField(
            model_name='programactivityitem',
            name='category',
            field=models.CharField(
                blank=True, max_length=60,
                verbose_name='Категория',
                help_text='Бейдж справа от стрелки (напр. «Технологии»).',
            ),
        ),
        *[
            migrations.AlterField(
                model_name='programactivityitem',
                name=f'category_{code}',
                field=models.CharField(
                    blank=True, null=True, max_length=60,
                    verbose_name='Категория',
                    help_text='Бейдж справа от стрелки (напр. «Технологии»).',
                ),
            )
            for code in LOCALES
        ],
        # Новые поля группы (translatable).
        *_make_char_ops(),
        *_make_text_ops(),
        # students_status — не переводится, это ключ.
        migrations.AddField(
            model_name='programactivityitem',
            name='students_status',
            field=models.CharField(
                blank=True, max_length=20,
                choices=[('recruiting', 'Идёт набор'), ('full', 'Мест нет')],
                verbose_name='Статус набора',
                help_text='Цветной хвостик после количества учеников.',
            ),
        ),
    ]
