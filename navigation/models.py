from django.db import models


class NavSection(models.Model):
    """
    Колонка мегаменю — группа пунктов с общим заголовком.
    Сейчас две: «Меню» (основные разделы) и «Жизнь школы» (доп).
    Структура общая для всех регионов; контент страниц per-region
    хранится в соответствующих CMS-моделях (HomePage и т.д.).
    """

    slug = models.SlugField(
        unique=True,
        max_length=32,
        help_text='Технический идентификатор секции: main, school-life. Только латиница.',
    )
    label = models.CharField('Заголовок', max_length=100)
    order = models.PositiveIntegerField(
        'Порядок',
        default=0,
        help_text='Колонки сортируются по возрастанию. Шаг 10 — оставляет место для вставки.',
    )

    class Meta:
        verbose_name = 'Секция мегаменю'
        verbose_name_plural = 'Секции мегаменю'
        ordering = ['order', 'slug']

    def __str__(self):
        return self.label or self.slug


class NavItem(models.Model):
    """
    Пункт навигации. Принадлежит секции мегаменю; флаг `is_top_nav`
    дополнительно выводит его в шапку слева от логотипа (на десктопе).

    `url_name` — Django namespace:name (`pages:about`). Пустой = заглушка,
    рендерится как `href="#"`. Так заведены пункты будущих разделов:
    в шапке они уже видны, при готовности страницы — заполняется url_name.
    """

    section = models.ForeignKey(
        NavSection,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Секция',
    )
    slug = models.SlugField(
        unique=True,
        max_length=64,
        help_text='Идентификатор для подсветки активной ссылки (active_page). Только латиница.',
    )
    label = models.CharField('Подпись', max_length=120)
    url_name = models.CharField(
        'URL name',
        max_length=120,
        blank=True,
        help_text='Django URL name, напр. pages:about. Пусто — пункт-заглушка с href="#".',
    )
    is_top_nav = models.BooleanField(
        'В шапке',
        default=False,
        help_text='Дополнительно выводить этот пункт в верхней навигации (десктоп). Дубликат в мегаменю остаётся.',
    )
    order = models.PositiveIntegerField('Порядок', default=0)
    is_published = models.BooleanField(
        'Опубликован',
        default=True,
        help_text='Снять флаг, чтобы временно убрать пункт из навигации, не удаляя.',
    )

    class Meta:
        verbose_name = 'Пункт навигации'
        verbose_name_plural = 'Пункты навигации'
        ordering = ['section__order', 'order', 'pk']

    def __str__(self):
        return f'{self.label} ({self.slug})'

    @property
    def is_placeholder(self):
        """True если ссылка ещё не привязана к view (url_name пустой)."""
        return not self.url_name
