from django.db import models
from imagekit.models import ImageSpecField


GALLERY_IMAGE_QUALITY = 85


class GalleryCategory(models.Model):
    """Категория-тема (Школьная жизнь / Робототехника / События). Глобальная
    справочная таблица — chip-фильтр на странице галереи. Альбомы привязываются
    к категории через FK."""

    slug = models.SlugField(
        'Slug',
        max_length=64,
        unique=True,
        help_text='Машинное имя категории (для ?category=...). Только латиница.',
    )
    name = models.CharField('Название', max_length=80)
    order = models.PositiveSmallIntegerField('Порядок', default=0)
    is_published = models.BooleanField('Опубликовано', default=True, db_index=True)

    class Meta:
        verbose_name = 'Категория фотогалереи'
        verbose_name_plural = 'Категории фотогалереи'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name or self.slug


class Album(models.Model):
    """Фотоальбом — region-scoped коллекция фото с темой (category).

    Архитектурно копирует BlogPost: один альбом = один «пост», фото внутри
    альбома сортируются по `-created_at` (новые сверху).
    """

    region = models.ForeignKey(
        'regions.Region',
        verbose_name='Регион',
        on_delete=models.PROTECT,
        related_name='gallery_albums',
    )
    category = models.ForeignKey(
        GalleryCategory,
        verbose_name='Тема (категория)',
        on_delete=models.PROTECT,
        related_name='albums',
        help_text='Тема альбома — chip-фильтр на странице галереи.',
    )

    slug = models.SlugField(
        'Slug',
        max_length=200,
        help_text='Сегмент в URL. Уникален в пределах региона.',
    )
    title = models.CharField('Название альбома', max_length=300)
    lead = models.TextField(
        'Описание',
        blank=True,
        help_text='Опционально: 1–2 предложения для подсказки в backoffice.',
    )
    cover_image = models.ImageField(
        'Обложка альбома',
        upload_to='gallery/albums/covers/',
        blank=True,
        null=True,
        help_text='Опциональная обложка для списка альбомов в backoffice. '
                  'На сайте не выводится (там общая лента фото).',
    )
    cover_image_webp = ImageSpecField(
        source='cover_image',
        format='WEBP',
        options={'quality': GALLERY_IMAGE_QUALITY},
    )
    cover_image_compressed = ImageSpecField(
        source='cover_image',
        options={'quality': GALLERY_IMAGE_QUALITY, 'optimize': True},
    )

    is_published = models.BooleanField('Опубликован', default=True, db_index=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        verbose_name = 'Фотоальбом'
        verbose_name_plural = 'Фотоальбомы'
        ordering = ['-created_at', '-pk']
        constraints = [
            models.UniqueConstraint(
                fields=['region', 'slug'],
                name='gallery_album_region_slug_unique',
            ),
        ]

    def __str__(self):
        return self.title or f'Album #{self.pk}'


class GalleryImage(models.Model):
    """Снимок в альбоме. Region и category резолвятся через `album.region`
    и `album.category` — поля на самом GalleryImage больше не используются
    (оставлены для миграционной совместимости, могут быть NULL в новых записях).
    """

    album = models.ForeignKey(
        Album,
        verbose_name='Альбом',
        on_delete=models.CASCADE,
        related_name='images',
        null=True,
        blank=True,
        help_text='Альбом, в который входит фотография. На паблике сортируется '
                  'по `-created_at` (свежие сверху).',
    )

    # Legacy: оставляем для совместимости с существующими записями. Резолв
    # на public странице теперь идёт через album.region / album.category.
    region = models.ForeignKey(
        'regions.Region',
        verbose_name='Регион (legacy)',
        on_delete=models.PROTECT,
        related_name='gallery_images',
    )
    category = models.ForeignKey(
        GalleryCategory,
        verbose_name='Категория (legacy)',
        on_delete=models.SET_NULL,
        related_name='images',
        null=True,
        blank=True,
        help_text='Устаревшее. Категория теперь привязана к Album.',
    )

    image = models.ImageField(
        'Изображение',
        upload_to='gallery/',
        null=True,
        help_text='Обязательное поле в админке. Записи без файла в выдачу не попадают.',
    )
    image_webp = ImageSpecField(
        source='image',
        format='WEBP',
        options={'quality': GALLERY_IMAGE_QUALITY},
    )
    image_compressed = ImageSpecField(
        source='image',
        options={'quality': GALLERY_IMAGE_QUALITY, 'optimize': True},
    )
    alt = models.CharField(
        'Alt-текст',
        max_length=300,
        blank=True,
        help_text='Для SEO/доступности. Если пусто — подставляется caption или slug категории.',
    )
    caption = models.CharField(
        'Подпись',
        max_length=300,
        blank=True,
    )

    is_wide = models.BooleanField(
        'Широкая карточка',
        default=False,
        help_text='Растягивает карточку на 2 колонки в мозаике. Авто-определяется '
                  'по aspect ratio при upload (>=1.4 → wide), можно переключить вручную.',
    )
    # Legacy: используется только для DnD reorder в backoffice (которого больше нет
    # в album-based UI). Сортировка на паблике — по -created_at.
    order = models.PositiveSmallIntegerField(
        'Порядок (legacy)',
        default=0,
        help_text='Устаревшее. Сортировка теперь по дате создания.',
    )
    is_published = models.BooleanField('Опубликовано', default=True, db_index=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Фото в галерее'
        verbose_name_plural = 'Фото в галерее'
        ordering = ['-created_at', '-pk']

    def __str__(self):
        return self.caption or self.alt or f'Image #{self.pk}'

    @property
    def alt_display(self) -> str:
        return (self.alt or '').strip() or (self.caption or '').strip() or ''

    @property
    def effective_region(self):
        """region теперь живёт на альбоме; fallback на legacy-поле."""
        if self.album_id:
            return self.album.region
        return self.region

    @property
    def effective_category(self):
        """category теперь живёт на альбоме."""
        if self.album_id:
            return self.album.category
        return self.category
