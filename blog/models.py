from django.db import models
from imagekit.models import ImageSpecField


BLOG_IMAGE_QUALITY = 85


class BlogCategory(models.Model):
    """Категория статей блога — chip-фильтр на списке.

    Region-scoped: набор категорий может отличаться между филиалами.
    Slug уникален в пределах региона.
    """

    region = models.ForeignKey(
        'regions.Region',
        verbose_name='Регион',
        on_delete=models.PROTECT,
        related_name='blog_categories',
    )
    slug = models.SlugField(
        'Slug',
        max_length=64,
        help_text='Машинное имя категории (для ?category=...). Только латиница.',
    )
    name = models.CharField('Название', max_length=80)
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Категория блога'
        verbose_name_plural = 'Категории блога'
        ordering = ['order', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['region', 'slug'],
                name='blog_category_region_slug_unique',
            ),
        ]

    def __str__(self):
        return self.name or self.slug


class BlogTag(models.Model):
    """Тег — выводится под текстом статьи и кликается в `?tag=<slug>`."""

    region = models.ForeignKey(
        'regions.Region',
        verbose_name='Регион',
        on_delete=models.PROTECT,
        related_name='blog_tags',
    )
    slug = models.SlugField('Slug', max_length=64)
    name = models.CharField('Название', max_length=80)
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Тег блога'
        verbose_name_plural = 'Теги блога'
        ordering = ['order', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['region', 'slug'],
                name='blog_tag_region_slug_unique',
            ),
        ]

    def __str__(self):
        return f'#{self.name or self.slug}'


class BlogPost(models.Model):
    """Статья блога. Region-scoped: статья пишется для конкретного филиала."""

    region = models.ForeignKey(
        'regions.Region',
        verbose_name='Регион',
        on_delete=models.PROTECT,
        related_name='blog_posts',
    )
    category = models.ForeignKey(
        BlogCategory,
        verbose_name='Категория',
        on_delete=models.PROTECT,
        related_name='posts',
    )
    tags = models.ManyToManyField(
        BlogTag,
        verbose_name='Теги',
        blank=True,
        related_name='posts',
    )

    slug = models.SlugField(
        'Slug',
        max_length=200,
        help_text='Сегмент в URL: my-post-title. Уникален в пределах региона.',
    )
    title = models.CharField('Заголовок (h1)', max_length=300)
    lead = models.TextField(
        'Лид',
        blank=True,
        help_text='Опционально: 1–2 предложения для превью и meta description.',
    )

    cover_image = models.ImageField(
        'Обложка',
        upload_to='blog/covers/',
        null=True,
        help_text='Обязательное поле в админке. Сид-миграции/legacy-записи '
                  'могут быть без файла — в шаблоне сработает fallback на '
                  'плейсхолдер «Нет фото».',
    )
    cover_image_webp = ImageSpecField(
        source='cover_image',
        format='WEBP',
        options={'quality': BLOG_IMAGE_QUALITY},
    )
    cover_image_compressed = ImageSpecField(
        source='cover_image',
        options={'quality': BLOG_IMAGE_QUALITY, 'optimize': True},
    )
    cover_caption = models.CharField(
        'Подпись под обложкой',
        max_length=300,
        blank=True,
        help_text='Опциональный figcaption под обложкой в теле статьи.',
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
        verbose_name = 'Статья блога'
        verbose_name_plural = 'Статьи блога'
        ordering = ['-published_at', '-pk']
        constraints = [
            models.UniqueConstraint(
                fields=['region', 'slug'],
                name='blog_post_region_slug_unique',
            ),
        ]

    def __str__(self):
        return self.title or f'BlogPost #{self.pk}'

    @property
    def cover_alt_display(self) -> str:
        return (self.cover_alt or '').strip() or self.title
