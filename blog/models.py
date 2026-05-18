from django.db import models
from imagekit.models import ImageSpecField


BLOG_IMAGE_QUALITY = 85


class BlogCategory(models.Model):
    """Категория статей блога — chip-фильтр на списке.

    Глобальная (общая для всех регионов). На ленте региона показываются
    только те категории, у которых есть опубликованные посты этого региона.
    """

    slug = models.SlugField(
        'Slug',
        max_length=64,
        unique=True,
        help_text='Машинное имя категории (для ?category=...). Только латиница.',
    )
    name = models.CharField('Название', max_length=80)
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Категория блога'
        verbose_name_plural = 'Категории блога'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name or self.slug


class BlogTag(models.Model):
    """Тег — выводится под текстом статьи и кликается в `?tag=<slug>`.
    Глобальный (общий для всех регионов)."""

    slug = models.SlugField('Slug', max_length=64, unique=True)
    name = models.CharField('Название', max_length=80)
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Тег блога'
        verbose_name_plural = 'Теги блога'
        ordering = ['order', 'name']

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
    author = models.ForeignKey(
        'team.TeamMember',
        verbose_name='Автор',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='blog_posts',
        help_text='Автор статьи из раздела «Команда». Доступны члены команды '
                  'того же региона. Если не указан — на сайте автор не выводится.',
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
        blank=True,
        null=True,
        help_text='Опционально. Если не загружена — на сайте покажется '
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

    seo_title = models.CharField(
        'SEO title (<title>)',
        max_length=80,
        blank=True,
        help_text='50–60 символов. Если пусто — fallback на title.',
    )
    seo_description = models.CharField(
        'SEO description (meta)',
        max_length=200,
        blank=True,
        help_text='150–160 символов. Если пусто — fallback на lead.',
    )
    og_title = models.CharField(
        'OG title',
        max_length=80,
        blank=True,
        help_text='Если пусто — fallback на seo_title → title.',
    )
    og_description = models.CharField(
        'OG description',
        max_length=300,
        blank=True,
        help_text='Если пусто — fallback на seo_description → lead.',
    )
    og_image = models.ImageField(
        'OG/share картинка',
        upload_to='blog/og/',
        blank=True,
        null=True,
        help_text='1200×630 для соцсетей. Если пусто — fallback на обложку поста.',
    )

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

    @property
    def main_gallery(self):
        """Главная inline-галерея поста (slug='main'). Рендерится после
        .content-redactor на public странице. Создаётся лениво при первом
        upload через backoffice."""
        return self.galleries.filter(slug='main').first()

    @property
    def effective_seo_title(self) -> str:
        return self.seo_title or (self.title or '').strip()

    @property
    def effective_seo_description(self) -> str:
        return self.seo_description or (self.lead or '').replace('\n', ' ').strip()

    @property
    def effective_og_title(self) -> str:
        return self.og_title or self.effective_seo_title

    @property
    def effective_og_description(self) -> str:
        return self.og_description or self.effective_seo_description

    @property
    def effective_og_image(self):
        return self.og_image or self.cover_image or None


class BlogGallery(models.Model):
    """Фотогалерея внутри статьи. Вставляется шорткодом
    `[[gallery slug=NAME]]` в `BlogPost.content` (см.
    `templatetags/blog_extras.render_galleries`).

    Один пост может содержать несколько галерей; slug уникален в пределах поста.
    """

    post = models.ForeignKey(
        BlogPost,
        verbose_name='Статья',
        on_delete=models.CASCADE,
        related_name='galleries',
    )
    slug = models.SlugField(
        'Slug',
        max_length=64,
        help_text='Ссылка в шорткоде: [[gallery slug=ЭТО]]. Уникален в пределах статьи.',
    )
    title = models.CharField(
        'Название',
        max_length=200,
        blank=True,
        help_text='Внутренняя метка для админки; не выводится на сайте.',
    )
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Фотогалерея'
        verbose_name_plural = 'Фотогалереи'
        ordering = ['order', 'pk']
        constraints = [
            models.UniqueConstraint(
                fields=['post', 'slug'],
                name='blog_gallery_post_slug_unique',
            ),
        ]

    def __str__(self):
        return self.title or self.slug or f'Gallery #{self.pk}'


class BlogGalleryImage(models.Model):
    """Снимок в галерее. Подпись и alt переводятся."""

    gallery = models.ForeignKey(
        BlogGallery,
        verbose_name='Галерея',
        on_delete=models.CASCADE,
        related_name='images',
    )
    image = models.ImageField('Изображение', upload_to='blog/galleries/')
    image_webp = ImageSpecField(
        source='image',
        format='WEBP',
        options={'quality': BLOG_IMAGE_QUALITY},
    )
    image_compressed = ImageSpecField(
        source='image',
        options={'quality': BLOG_IMAGE_QUALITY, 'optimize': True},
    )
    caption = models.CharField(
        'Подпись',
        max_length=300,
        blank=True,
        help_text='Опциональный figcaption под картинкой.',
    )
    alt = models.CharField(
        'Alt-текст',
        max_length=300,
        blank=True,
        help_text='Для SEO/доступности. Если пусто — подставляется подпись или название галереи.',
    )
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Фото в галерее'
        verbose_name_plural = 'Фото в галерее'
        ordering = ['order', 'pk']

    def __str__(self):
        return self.caption or f'Image #{self.pk}'

    @property
    def alt_display(self) -> str:
        return (self.alt or '').strip() or (self.caption or '').strip() or str(self.gallery)
