from django.db import models
from imagekit.models import ImageSpecField


EVENT_IMAGE_QUALITY = 85


class Event(models.Model):
    """Мероприятие. Region-scoped: разный набор в каждом филиале.

    В отличие от `blog.BlogPost`, у мероприятий нет деления на категории
    и теги — это плоская лента анонсов/отчётов.
    """

    region = models.ForeignKey(
        'regions.Region',
        verbose_name='Регион',
        on_delete=models.PROTECT,
        related_name='events',
    )

    slug = models.SlugField(
        'Slug',
        max_length=200,
        help_text='Сегмент в URL: open-day-2026. Уникален в пределах региона.',
    )
    title = models.CharField('Заголовок (h1)', max_length=300)
    lead = models.TextField(
        'Лид',
        blank=True,
        help_text='Опционально: 1–2 предложения для превью и meta description.',
    )

    cover_image = models.ImageField(
        'Обложка',
        upload_to='events/covers/',
        null=True,
        help_text='Обязательное поле в админке. Сид-миграции/legacy-записи '
                  'могут быть без файла — в шаблоне сработает fallback на '
                  'плейсхолдер «Нет фото».',
    )
    cover_image_webp = ImageSpecField(
        source='cover_image',
        format='WEBP',
        options={'quality': EVENT_IMAGE_QUALITY},
    )
    cover_image_compressed = ImageSpecField(
        source='cover_image',
        options={'quality': EVENT_IMAGE_QUALITY, 'optimize': True},
    )
    cover_caption = models.CharField(
        'Подпись под обложкой',
        max_length=300,
        blank=True,
    )
    cover_alt = models.CharField(
        'Alt-текст обложки',
        max_length=300,
        blank=True,
        help_text='Для SEO/доступности. Если пусто — подставляется title.',
    )

    content = models.TextField(
        'Содержимое (HTML)',
        help_text='HTML рендерится через |safe. Используй h2/h3/h4, p, ul/ol/li, '
                  'blockquote+cite, a, img, figure+figcaption, small.',
    )

    is_published = models.BooleanField('Опубликовано', default=True, db_index=True)
    published_at = models.DateTimeField(
        'Дата публикации',
        db_index=True,
        help_text='Сортировка ленты и показ даты на карточке.',
    )
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Мероприятие'
        verbose_name_plural = 'Мероприятия'
        ordering = ['-published_at', '-pk']
        constraints = [
            models.UniqueConstraint(
                fields=['region', 'slug'],
                name='event_region_slug_unique',
            ),
        ]

    def __str__(self):
        return self.title or f'Event #{self.pk}'

    @property
    def cover_alt_display(self) -> str:
        return (self.cover_alt or '').strip() or self.title
