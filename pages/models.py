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


class ContactsPage(models.Model):
    """
    Содержимое страницы «Контакты» региона. Singleton per region (OneToOne).

    Текстовые поля переводятся через modeltranslation (см. translation.py).
    Отделы (Поступление/Партнёрство/Вакансии и т.д.) — inline-модель
    ContactsDepartment, чтобы редактор мог добавлять/убирать/переупорядочивать.
    """

    region = models.OneToOneField(
        'regions.Region',
        verbose_name='Регион',
        on_delete=models.PROTECT,
        related_name='contacts_page',
    )

    # --- Intro ---
    intro_title = models.CharField('Заголовок', max_length=120)
    intro_text = models.TextField(
        'Описание',
        help_text='Параграф под заголовком.',
    )

    # --- Office card (overlay над картой) ---
    office_name = models.CharField('Название офиса', max_length=120)
    office_address = models.CharField('Адрес', max_length=255)
    office_hours = models.CharField(
        'Часы работы офиса',
        max_length=120,
        help_text='Напр. «Пн–Пт, 09:00–18:00».',
    )

    # --- Map (Leaflet, CartoDB light_nolabels) ---
    latitude = models.DecimalField(
        'Широта',
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        help_text='Десятичные градусы, напр. 51.093900. '
                  'Если широта или долгота пуста — карта не отрисуется, '
                  'покажется серая заглушка.',
    )
    longitude = models.DecimalField(
        'Долгота',
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        help_text='Десятичные градусы, напр. 71.401100.',
    )
    map_zoom = models.PositiveSmallIntegerField(
        'Zoom карты',
        default=16,
        help_text='Целое 1–19 (Leaflet/CartoDB). 16 — улица + здание.',
    )

    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Страница «Контакты»'
        verbose_name_plural = 'Страницы «Контакты»'

    def __str__(self):
        return f'Контакты — {self.region}'

    @property
    def coordinates(self) -> str:
        """
        Координаты в формате `lat,lng` для data-атрибута карты Leaflet.

        Пусто → пустая строка (шаблон рендерит серую заглушку).
        Форматирование (6 знаков, точка-разделитель, запятая между значениями)
        идёт здесь, чтобы шаблон оставался без логики и JS не парсил локали.
        """
        if self.latitude is None or self.longitude is None:
            return ''
        return f'{self.latitude:.6f},{self.longitude:.6f}'


class ContactsDepartment(models.Model):
    """Колонка-отдел на странице контактов (Поступление, Партнёрство, Вакансии…)."""

    contacts_page = models.ForeignKey(
        ContactsPage,
        verbose_name='Страница «Контакты»',
        on_delete=models.CASCADE,
        related_name='departments',
    )
    title = models.CharField('Название отдела', max_length=120)
    description = models.TextField('Описание')
    phone = models.CharField(
        'Телефон',
        max_length=40,
        blank=True,
        help_text='Если пусто — строка не отрисуется.',
    )
    email = models.EmailField('Email', blank=True)
    hours = models.CharField(
        'Часы работы',
        max_length=120,
        blank=True,
        help_text='Напр. «Пн–Пт, 09:00–18:00». Если пусто — строка скрыта.',
    )
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Отдел контактов'
        verbose_name_plural = 'Отделы контактов'
        ordering = ['order', 'pk']

    def __str__(self):
        return self.title or f'Department #{self.pk}'
