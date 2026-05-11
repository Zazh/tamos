from django.db import models
from imagekit.models import ImageSpecField


# Hero — минимальная компрессия (большой decorative фасад, важна детализация).
HERO_QUALITY = 95
# Карусель — обычная компрессия, картинки крутятся быстро.
GALLERY_QUALITY = 80


class HomePage(models.Model):
    """
    Содержимое главной страницы региона. Singleton per region (OneToOne).

    Видео и hero-фон — FileField/ImageField (язык-нейтральные).
    Текстовые поля переводятся через modeltranslation (см. translation.py).
    Перенос строки в hero_title рендерится как отдельный <span class="hero-fit">
    (важно для fitty-подгонки шрифта на мобиле).
    """

    region = models.OneToOneField(
        'regions.Region',
        verbose_name='Регион',
        on_delete=models.PROTECT,
        related_name='home_page',
    )

    # --- Hero ---
    hero_image = models.ImageField(
        'Фон hero',
        upload_to='home/hero/',
        blank=True,
        null=True,
        help_text='Фоновое изображение под hero-блоком (например, здание школы). '
                  'WebP и сжатая JPEG/PNG версии генерируются автоматически.',
    )
    hero_image_webp = ImageSpecField(
        source='hero_image',
        format='WEBP',
        options={'quality': HERO_QUALITY},
    )
    hero_image_compressed = ImageSpecField(
        source='hero_image',
        options={'quality': HERO_QUALITY, 'optimize': True},
    )
    hero_badge_text = models.CharField(
        'Бадж над заголовком',
        max_length=120,
        help_text='Маленький ярлычок над h1.',
    )
    hero_title = models.TextField(
        'Заголовок hero (h1)',
        help_text='Каждая строка → отдельный <span class="hero-fit"> '
                  '(на мобиле fitty подгоняет шрифт построчно).',
    )
    hero_subtitle = models.TextField(
        'Подзаголовок hero (h2)',
        help_text='Перенос строки = <br class="hidden md:block"> '
                  '(виден только на десктопе).',
    )
    hero_cta_primary_text = models.CharField('Текст основной CTA', max_length=80)
    hero_cta_secondary_text = models.CharField('Текст вторичной CTA', max_length=80)

    # --- About-Us section ---
    about_label = models.CharField(
        'Лейбл секции «О нас»',
        max_length=80,
        help_text='Маленькая надпись над заголовком (например, «Кому подходит»).',
    )
    about_title = models.TextField(
        'Заголовок секции «О нас»',
        help_text='Перенос строки = <br>.',
    )
    about_body = models.TextField(
        'Текст секции «О нас»',
        help_text='Пустая строка = новый параграф.',
    )

    # --- Video ---
    video_file = models.FileField(
        'Видео',
        upload_to='home/video/',
        blank=True,
        null=True,
        help_text='Mp4 для видео-блока. Если пусто — блок не отрисовывается.',
    )

    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Главная страница'
        verbose_name_plural = 'Главные страницы'

    def __str__(self):
        return f'Главная — {self.region}'


class HomeGalleryImage(models.Model):
    """Картинка карусели на главной. Заливается через inline в админке HomePage."""

    home_page = models.ForeignKey(
        HomePage,
        verbose_name='Главная страница',
        on_delete=models.CASCADE,
        related_name='gallery',
    )
    image = models.ImageField('Картинка', upload_to='home/gallery/')
    image_webp = ImageSpecField(
        source='image',
        format='WEBP',
        options={'quality': GALLERY_QUALITY},
    )
    image_compressed = ImageSpecField(
        source='image',
        options={'quality': GALLERY_QUALITY, 'optimize': True},
    )
    alt_text = models.CharField('Alt-текст', max_length=200, blank=True)
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Картинка галереи'
        verbose_name_plural = 'Картинки галереи'
        ordering = ['order', 'pk']

    def __str__(self):
        return self.alt_text or f'Image #{self.pk}'
