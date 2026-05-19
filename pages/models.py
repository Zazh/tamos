from django.db import models
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit


# Hero — минимальная компрессия (большой decorative фасад, важна детализация).
HERO_QUALITY = 95
# Карусель — обычная компрессия, картинки крутятся быстро.
GALLERY_QUALITY = 80
# Обложки статичных страниц — как у блога.
FLAT_IMAGE_QUALITY = 85
# Карусель на главной — max 352px CSS slot, 2× retina = ~700, округлим до 800.
GALLERY_MAX_DIMENSION = 800


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
        help_text='HTML-разметка (рендерится через |safe). Используй '
                  '<span class="hero-fit">…</span> для построчной подгонки '
                  'шрифта на мобиле; внутри можно <span class="hero-break">…</span> '
                  '(десктопный перенос) и <span class="text-gold">…</span> для акцента. '
                  'Пример: <span class="hero-fit">Лучшее образование</span>'
                  '<span class="hero-fit"><span class="hero-break">для будущего</span></span>'
                  '<span class="hero-fit">ребёнка</span>',
    )
    hero_subtitle = models.TextField(
        'Подзаголовок hero (h2)',
        help_text='Перенос строки = <br class="hidden md:block"> '
                  '(виден только на десктопе).',
    )
    hero_cta_primary_text = models.CharField('Текст основной CTA', max_length=80)
    hero_cta_primary_modal_title = models.CharField(
        'Заголовок модалки primary CTA',
        max_length=80,
        blank=True,
        help_text='Если пусто — fallback на текст кнопки.',
    )
    hero_cta_secondary_text = models.CharField('Текст вторичной CTA', max_length=80)
    hero_cta_secondary_modal_title = models.CharField(
        'Заголовок модалки secondary CTA',
        max_length=80,
        blank=True,
        help_text='Если пусто — fallback на текст кнопки.',
    )

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

    # --- Шоурил (видео) ---
    video_file = models.FileField(
        'Шоурил',
        upload_to='home/video/',
        blank=True,
        null=True,
        help_text='Mp4 для видео-блока. Если пусто — блок не отрисовывается.',
    )
    video_poster = models.ImageField(
        'Poster (1-й кадр)',
        upload_to='home/video_posters/',
        blank=True,
        null=True,
        help_text='Автоматически генерируется из 1-й секунды видео при сохранении. '
                  'Показывается до старта воспроизведения (важен для UX на медленном '
                  'соединении и для SEO).',
    )
    video_poster_webp = ImageSpecField(
        source='video_poster',
        format='WEBP',
        options={'quality': 85},
    )

    # --- SEO ---
    seo_title = models.CharField(
        'SEO title (<title>)',
        max_length=80,
        blank=True,
        help_text='50–60 символов. Если пусто — fallback на hero_title.',
    )
    seo_description = models.CharField(
        'SEO description (meta)',
        max_length=200,
        blank=True,
        help_text='150–160 символов. Если пусто — fallback на hero_subtitle.',
    )
    og_image = models.ImageField(
        'OG/share картинка',
        upload_to='home/og/',
        blank=True,
        null=True,
        help_text='1200×630 для соцсетей. Если пусто — fallback на hero_image '
                  '(но он прозрачный — в соцсетях будет некрасиво).',
    )
    og_title = models.CharField(
        'OG title',
        max_length=80,
        blank=True,
        help_text='Если пусто — fallback на seo_title → hero_title.',
    )
    og_description = models.CharField(
        'OG description',
        max_length=300,
        blank=True,
        help_text='Если пусто — fallback на seo_description → hero_subtitle.',
    )

    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Главная страница'
        verbose_name_plural = 'Главные страницы'

    def __str__(self):
        return f'Главная — {self.region}'

    def save(self, *args, **kwargs):
        # Хранит state до save — после super().save() сравним и решим, нужна
        # ли генерация poster'а.
        video_changed = False
        if self.pk:
            try:
                old = type(self).objects.only('video_file').get(pk=self.pk)
                video_changed = (old.video_file.name or '') != (self.video_file.name or '')
            except type(self).DoesNotExist:
                video_changed = True
        else:
            video_changed = bool(self.video_file)

        super().save(*args, **kwargs)

        if video_changed and self.video_file:
            self._generate_video_poster()

    def _generate_video_poster(self):
        """Извлечь 1-й кадр (на 1-й секунде) через ffmpeg, сохранить в video_poster.

        Если ffmpeg недоступен или видео битое — silent failure (poster останется
        пустым, frontend покажет fallback hero_image).
        """
        import subprocess, tempfile, os
        from django.core.files import File

        video_path = self.video_file.path
        if not os.path.exists(video_path):
            return

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # -ss 1 (seek to 1 second) — обычно после fade-in / интро
            # -vframes 1 — взять один кадр
            # -q:v 2 — высокое JPEG качество
            result = subprocess.run(
                ['ffmpeg', '-y', '-ss', '1', '-i', video_path,
                 '-vframes', '1', '-q:v', '2',
                 '-vf', "scale='min(1920,iw)':-2",
                 tmp_path],
                capture_output=True, timeout=30,
            )
            if result.returncode != 0 or not os.path.getsize(tmp_path):
                return
            base = os.path.splitext(os.path.basename(video_path))[0]
            with open(tmp_path, 'rb') as f:
                self.video_poster.save(f'{base}_poster.jpg', File(f), save=False)
            type(self).objects.filter(pk=self.pk).update(video_poster=self.video_poster.name)
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return
        finally:
            try: os.unlink(tmp_path)
            except OSError: pass

    @property
    def effective_seo_title(self) -> str:
        from django.utils.html import strip_tags
        return self.seo_title or strip_tags(self.hero_title or '').strip()

    @property
    def effective_seo_description(self) -> str:
        return self.seo_description or (self.hero_subtitle or '').replace('\n', ' ').strip()

    @property
    def effective_og_title(self) -> str:
        return self.og_title or self.effective_seo_title

    @property
    def effective_og_description(self) -> str:
        return self.og_description or self.effective_seo_description

    @property
    def effective_og_image(self):
        return self.og_image or self.hero_image

    @property
    def effective_cta_primary_modal_title(self) -> str:
        return self.hero_cta_primary_modal_title or self.hero_cta_primary_text

    @property
    def effective_cta_secondary_modal_title(self) -> str:
        return self.hero_cta_secondary_modal_title or self.hero_cta_secondary_text


class HomeGalleryImage(models.Model):
    """Картинка карусели на главной. Заливается через DnD-grid в backoffice.

    `orientation` определяется автоматически по соотношению сторон при save()
    и задаёт CSS-слот в `carousel.css` (.carousel-item-wide / -tall / -square).
    Менеджер расставляет порядок через DnD; warning подсвечивается, если
    орientation не подходит под расчётный slot позиции.
    """

    class Orientation(models.TextChoices):
        WIDE = 'wide', 'Широкая'      # ratio > 1.15  → слот 342×223
        TALL = 'tall', 'Высокая'      # ratio < 0.95  → слот 325×352
        SQUARE = 'square', 'Квадратная'

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
        processors=[ResizeToFit(GALLERY_MAX_DIMENSION, GALLERY_MAX_DIMENSION, upscale=False)],
    )
    image_compressed = ImageSpecField(
        source='image',
        options={'quality': GALLERY_QUALITY, 'optimize': True},
        processors=[ResizeToFit(GALLERY_MAX_DIMENSION, GALLERY_MAX_DIMENSION, upscale=False)],
    )
    orientation = models.CharField(
        'Ориентация',
        max_length=8,
        choices=Orientation.choices,
        default=Orientation.SQUARE,
        help_text='Определяется автоматически при загрузке (wide/tall/square).',
    )
    alt_text = models.CharField('Alt-текст', max_length=200, blank=True)
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Картинка галереи'
        verbose_name_plural = 'Картинки галереи'
        ordering = ['order', 'pk']

    def __str__(self):
        return self.alt_text or f'Image #{self.pk}'

    def save(self, *args, **kwargs):
        if self.image and (
            not self.pk
            or 'image' in (kwargs.get('update_fields') or ())
            or self._image_changed()
        ):
            self.orientation = self._detect_orientation()
        super().save(*args, **kwargs)

    def _image_changed(self) -> bool:
        if not self.pk:
            return True
        try:
            old = type(self).objects.only('image').get(pk=self.pk)
        except type(self).DoesNotExist:
            return True
        return old.image.name != self.image.name

    def _detect_orientation(self) -> str:
        """Открыть оригинал через Pillow, вычислить ratio width/height.

        - ratio > 1.15 → wide (горизонтальная)
        - ratio < 0.95 → tall (вертикальная)
        - между      → square (квадратная)

        Если файл недоступен / не открывается — square (безопасный дефолт).
        """
        from PIL import Image, UnidentifiedImageError
        try:
            with Image.open(self.image) as im:
                w, h = im.size
        except (FileNotFoundError, UnidentifiedImageError, OSError):
            return self.Orientation.SQUARE
        if h == 0:
            return self.Orientation.SQUARE
        ratio = w / h
        if ratio > 1.15:
            return self.Orientation.WIDE
        if ratio < 0.95:
            return self.Orientation.TALL
        return self.Orientation.SQUARE

    @classmethod
    def strict_zip_arrange(cls, images):
        """Расставить картинки в строгом порядке: wide → tall → wide → tall →…

        - Сначала идут чередующиеся пары (W, T, W, T, …) пока есть запас обоих
        - Хвост (оставшиеся wide или tall) приклеивается в конец
        - Square — всегда в конец

        Используется в:
        - backoffice upload (auto-arrange после загрузки)
        - frontend HomeView (принудительный порядок в карусели)

        Не сохраняет в БД — возвращает упорядоченный список. Порядок внутри
        каждой группы сохраняется (по текущему order, потом по pk).
        """
        sorted_imgs = sorted(images, key=lambda i: (i.order, i.pk))
        wide = [i for i in sorted_imgs if i.orientation == cls.Orientation.WIDE]
        tall = [i for i in sorted_imgs if i.orientation == cls.Orientation.TALL]
        square = [i for i in sorted_imgs if i.orientation == cls.Orientation.SQUARE]

        result = []
        while wide and tall:
            result.append(wide.pop(0))
            result.append(tall.pop(0))
        result.extend(wide)
        result.extend(tall)
        result.extend(square)
        return result


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

    # --- SEO ---
    seo_title = models.CharField(
        'SEO title (<title>)',
        max_length=80,
        blank=True,
        help_text='50–60 символов. Если пусто — fallback на intro_title.',
    )
    seo_description = models.CharField(
        'SEO description (meta)',
        max_length=200,
        blank=True,
        help_text='150–160 символов. Если пусто — fallback на intro_text.',
    )
    og_image = models.ImageField(
        'OG/share картинка',
        upload_to='contacts/og/',
        blank=True,
        null=True,
        help_text='1200×630 для соцсетей. Если пусто — на сайте OG-картинки '
                  'не будет (контакты — обычно не share-target).',
    )
    og_title = models.CharField(
        'OG title',
        max_length=80,
        blank=True,
        help_text='Если пусто — fallback на seo_title → intro_title.',
    )
    og_description = models.CharField(
        'OG description',
        max_length=300,
        blank=True,
        help_text='Если пусто — fallback на seo_description → intro_text.',
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

    @property
    def effective_seo_title(self) -> str:
        return self.seo_title or (self.intro_title or '').strip()

    @property
    def effective_seo_description(self) -> str:
        return self.seo_description or (self.intro_text or '').replace('\n', ' ').strip()

    @property
    def effective_og_title(self) -> str:
        return self.og_title or self.effective_seo_title

    @property
    def effective_og_description(self) -> str:
        return self.og_description or self.effective_seo_description

    @property
    def effective_og_image(self):
        return self.og_image or None


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


class FlatPage(models.Model):
    """
    Статичная контентная страница per-region: «О нас», «Школьная форма»,
    «Питание», «Политика конфиденциальности» и т.п.

    Шаблон `templates/pages/flat.html` — упрощённый blog-detail
    (без даты, share, тегов, хлебных крошек и related-блока).

    Линкуется в навигацию через `NavItem.flat_page` (FK). NavItem.url_name
    у таких пунктов остаётся пустым — резолв идёт по FK.
    """

    region = models.ForeignKey(
        'regions.Region',
        verbose_name='Регион',
        on_delete=models.PROTECT,
        related_name='flat_pages',
    )

    slug = models.SlugField(
        'Slug',
        max_length=80,
        help_text='Сегмент URL: about, uniform, privacy и т.п. '
                  'Уникален в пределах региона.',
    )
    title = models.CharField('Заголовок (h1)', max_length=200)
    lead = models.TextField(
        'Лид',
        blank=True,
        help_text='Опционально: 1–2 предложения для превью и meta description.',
    )

    cover_image = models.ImageField(
        'Обложка',
        upload_to='pages/flat/covers/',
        blank=True,
        null=True,
        help_text='Опциональная обложка над контентом. Если пусто — секция '
                  'с картинкой не отрисовывается.',
    )
    cover_image_webp = ImageSpecField(
        source='cover_image',
        format='WEBP',
        options={'quality': FLAT_IMAGE_QUALITY},
    )
    cover_image_compressed = ImageSpecField(
        source='cover_image',
        options={'quality': FLAT_IMAGE_QUALITY, 'optimize': True},
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

    is_published = models.BooleanField('Опубликована', default=True, db_index=True)
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
        upload_to='pages/flat/og/',
        blank=True,
        null=True,
        help_text='1200×630 для соцсетей. Если пусто — fallback на обложку страницы.',
    )

    class Meta:
        verbose_name = 'Статичная страница'
        verbose_name_plural = 'Статичные страницы'
        ordering = ['region', 'slug']
        constraints = [
            models.UniqueConstraint(
                fields=['region', 'slug'],
                name='pages_flatpage_region_slug_unique',
            ),
        ]

    def __str__(self):
        return f'{self.title} — {self.region}'

    @property
    def cover_alt_display(self) -> str:
        return (self.cover_alt or '').strip() or self.title

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
