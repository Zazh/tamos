from django.db import models


# Маппинг префикса origin → broad category. Авто-проставляется
# при создании Lead (см. save). Префикс сравнивается с `startswith`,
# поэтому `admission-cambridge-grade-1` попадёт в ADMISSION,
# `program-hero` — в PROGRAM, и т.д.
_ORIGIN_PREFIX_TO_CATEGORY = (
    ('admission', 'admission'),
    ('program', 'program'),
    ('activity', 'activity'),
)


class Lead(models.Model):
    """Заявка из модального окна обратной связи.

    Региональный scope — обязательный: `region` = `request.region` страницы,
    с которой кликнули. Менеджер региона видит только свои заявки
    (RegionScopedAdminMixin); superuser — все.

    Категория автоматически выводится из `origin` (см. `_ORIGIN_PREFIX_TO_CATEGORY`)
    при создании. Editor может переопределить вручную в админке —
    при последующих сохранениях значение НЕ переписывается.
    """

    class Category(models.TextChoices):
        ADMISSION = 'admission', 'Поступление'
        PROGRAM = 'program', 'Программа'
        ACTIVITY = 'activity', 'Внеклассные'
        GENERAL = 'general', 'Общая'

    class Status(models.TextChoices):
        NEW = 'new', 'Новая'
        IN_PROGRESS = 'in_progress', 'В работе'
        DONE = 'done', 'Закрыта успешно'
        REJECTED = 'rejected', 'Отказ/спам'

    # --- Источник ---
    region = models.ForeignKey(
        'regions.Region',
        verbose_name='Регион',
        on_delete=models.PROTECT,
        related_name='leads',
        help_text='Регион страницы, с которой пришла заявка. '
                  'Не путать с городом, выбранным в форме.',
    )
    origin = models.CharField(
        'Источник (origin)',
        max_length=120,
        blank=True,
        db_index=True,
        help_text='Семантический тег места вызова модалки: hero, '
                  'program-hero, admission-cambridge-grade-1, '
                  'activity-12-group-3 и т.п.',
    )
    title = models.CharField(
        'Заголовок модалки',
        max_length=200,
        blank=True,
        help_text='Контекстный заголовок, который видел пользователь '
                  '(напр. «Запишитесь на бесплатную консультацию»).',
    )
    category = models.CharField(
        'Категория',
        max_length=20,
        choices=Category.choices,
        default=Category.GENERAL,
        db_index=True,
        help_text='Авто-вывод из origin при создании. После можно '
                  'переопределить вручную.',
    )

    # --- Контакт ---
    name = models.CharField('Имя', max_length=120)
    phone = models.CharField('Телефон', max_length=40)
    city = models.CharField(
        'Город (из формы)',
        max_length=80,
        blank=True,
        help_text='Если модалка открывалась с data-feedback-city, '
                  'тут выбор пользователя (Астана/Актау/…).',
    )

    # --- CRM-flow ---
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        db_index=True,
    )
    manager_note = models.TextField(
        'Заметка менеджера',
        blank=True,
        help_text='Что по звонку, договорённости, отказ и причина.',
    )

    # --- Согласие на обработку (под политикой конфиденциальности) ---
    consented_at = models.DateTimeField(
        'Согласие получено',
        auto_now_add=True,
        help_text='Момент отправки формы = момент согласия. '
                  'Снимает споры «я не давал согласия».',
    )
    policy_version = models.CharField(
        'Версия политики',
        max_length=20,
        default='v1',
        help_text='Фиксируется при создании. Меняется через настройки '
                  'при выпуске новой редакции политики.',
    )

    # --- Audit (для дебага/антиспама в будущем) ---
    ip_address = models.GenericIPAddressField('IP', null=True, blank=True)
    user_agent = models.CharField('User-Agent', max_length=300, blank=True)

    created_at = models.DateTimeField('Создана', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('Обновлена', auto_now=True)

    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.phone}) — {self.get_status_display()}'

    def save(self, *args, **kwargs):
        # Авто-категория только при создании — чтобы ручная правка в админке
        # не перетиралась при последующих сохранениях.
        if self._state.adding and self.category == self.Category.GENERAL and self.origin:
            for prefix, cat in _ORIGIN_PREFIX_TO_CATEGORY:
                if self.origin.startswith(prefix):
                    self.category = cat
                    break
        super().save(*args, **kwargs)
