from django.db import models
from imagekit.models import ImageSpecField


GALLERY_IMAGE_QUALITY = 85


class GalleryCategory(models.Model):
    """Категория фотографии — chip-фильтр на странице галереи.

    Глобальная (не region-scoped): набор тем одинаков для всех филиалов.
    """

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


class GalleryImage(models.Model):
    """Снимок в публичной фотогалерее. Region-scoped: у каждого филиала
    свой набор фото; фильтр-чипы наверху страницы — общие категории.
    """

    region = models.ForeignKey(
        'regions.Region',
        verbose_name='Регион',
        on_delete=models.PROTECT,
        related_name='gallery_images',
    )
    category = models.ForeignKey(
        GalleryCategory,
        verbose_name='Категория',
        on_delete=models.SET_NULL,
        related_name='images',
        null=True,
        blank=True,
        help_text='Опционально. Влияет только на chip-фильтр на странице.',
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
        help_text='Растягивает карточку на 2 колонки в мозаике (mosaic-card-wide).',
    )
    order = models.PositiveSmallIntegerField(
        'Порядок',
        default=0,
        help_text='Чем меньше — тем выше. При равных — по дате (свежие выше).',
    )
    is_published = models.BooleanField('Опубликовано', default=True, db_index=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Фото в галерее'
        verbose_name_plural = 'Фото в галерее'
        ordering = ['order', '-created_at', '-pk']

    def __str__(self):
        return self.caption or self.alt or f'Image #{self.pk}'

    @property
    def alt_display(self) -> str:
        return (self.alt or '').strip() or (self.caption or '').strip() or ''
