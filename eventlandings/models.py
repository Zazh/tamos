from datetime import datetime

from django.db import models
from django.utils import timezone
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit

from core.gallery import OrientedGalleryImage

# Карусель «О Space School» — как у HomeGalleryImage (слот ≤ 352px, 2× retina).
GALLERY_QUALITY = 80
GALLERY_MAX_DIMENSION = 800


def _thousands(value: int) -> str:
    """18990 → '18 990' с неразрывным пробелом между разрядами."""
    return f'{value:,}'.replace(',', '\xa0')


class EventLanding(models.Model):
    """Лендинг события (день открытых дверей, воркшоп, семинар).

    Region-scoped; живёт рядом с лентой новостей `events.Event`. «Прошло» —
    сейчас позже конца последнего дня (`is_past`). Текст блока «Школа» —
    из `pages.HomePage` региона, своих полей нет.
    """

    region = models.ForeignKey(
        'regions.Region',
        verbose_name='Регион',
        on_delete=models.PROTECT,
        related_name='event_landings',
    )
    slug = models.SlugField(
        'Slug',
        max_length=200,
        help_text='Сегмент URL: cambridge-day. Уникален в пределах региона',
    )
    is_published = models.BooleanField('Опубликовано', default=False, db_index=True)

    title = models.CharField('Заголовок (h1)', max_length=200)
    badge_text = models.CharField('Бейдж', max_length=80, blank=True)
    lead = models.TextField('Лид', blank=True)

    audience_title = models.CharField('«Для кого» — заголовок', max_length=200, blank=True)
    audience_text = models.TextField('«Для кого» — текст', blank=True)
    goal = models.TextField('Цель события', blank=True)

    program_title = models.CharField('Программа — заголовок', max_length=200, blank=True)
    materials_title = models.CharField('Материалы — заголовок', max_length=200, blank=True)
    leaders_title = models.CharField('Ведущие — заголовок', max_length=200, blank=True)
    leaders_lead = models.TextField('Ведущие — текст', blank=True)

    reg_title = models.CharField(
        'Регистрация — заголовок',
        max_length=200,
        blank=True,
        help_text='Перенос строки = новая строка заголовка',
    )
    reg_text = models.TextField('Регистрация — текст', blank=True)
    form_title = models.CharField('Форма — заголовок', max_length=200, blank=True)
    form_lead = models.TextField('Форма — подзаголовок', blank=True)
    form_note = models.CharField(
        'Форма — текст после отправки',
        max_length=300,
        blank=True,
        help_text='Показывается в окне «Заявка принята».',
    )
    cta_text = models.CharField('Текст кнопки регистрации', max_length=80, blank=True)
    price_note = models.CharField(
        'Примечание к цене',
        max_length=200,
        blank=True,
        help_text='Под ценой в карточке даты: «за участника за два дня».',
    )

    is_paid = models.BooleanField('Платное', default=False)
    price = models.PositiveIntegerField(
        'Цена',
        null=True,
        blank=True,
        help_text='₸, целое; пусто у бесплатных',
    )
    show_parent_checkbox = models.BooleanField(
        'Чекбокс «родитель ученика»',
        default=False,
        help_text='Чекбокс „Я родитель ученика Space School“ в форме',
    )

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

    leaders = models.ManyToManyField(
        'team.TeamMember',
        verbose_name='Ведущие',
        blank=True,
        related_name='event_landings',
        help_text='Участники «Команды» того же региона; порядок — как в «Команде».',
    )

    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Лендинг события'
        verbose_name_plural = 'Лендинги событий'
        ordering = ['-created_at', '-pk']
        constraints = [
            models.UniqueConstraint(
                fields=['region', 'slug'],
                name='eventlanding_region_slug_unique',
            ),
        ]

    def __str__(self):
        return self.title or f'EventLanding #{self.pk}'

    # ── Даты ─────────────────────────────────────────────────────────────
    def _ordered_days(self):
        # prefetch_related('days') уважает Meta.ordering дня — без лишних запросов.
        return list(self.days.all())

    @property
    def first_day(self):
        days = self._ordered_days()
        return days[0] if days else None

    @property
    def last_day(self):
        days = self._ordered_days()
        return days[-1] if days else None

    @property
    def starts_at(self):
        day = self.first_day
        if day is None:
            return None
        return timezone.make_aware(datetime.combine(day.date, day.start))

    @property
    def ends_at(self):
        day = self.last_day
        if day is None:
            return None
        return timezone.make_aware(datetime.combine(day.date, day.end))

    @property
    def is_past(self) -> bool:
        ends = self.ends_at
        return ends is not None and timezone.now() > ends

    # ── Цена ─────────────────────────────────────────────────────────────
    @property
    def price_display(self) -> str:
        if self.price is None:
            return ''
        return f'{_thousands(self.price)}\xa0₸'

    # ── SEO ──────────────────────────────────────────────────────────────
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

    # ── Ведущие ──────────────────────────────────────────────────────────
    @property
    def leaders_published(self):
        return self.leaders.filter(is_published=True).order_by('order', 'pk')


class EventLandingDay(models.Model):
    landing = models.ForeignKey(
        EventLanding,
        verbose_name='Лендинг',
        on_delete=models.CASCADE,
        related_name='days',
    )
    date = models.DateField('Дата')
    start = models.TimeField('Начало')
    end = models.TimeField('Окончание')
    label = models.CharField(
        'Подпись дня',
        max_length=80,
        blank=True,
        help_text='Напр. „День 1 · 21 ноября“; пусто — подпись строится из даты',
    )

    class Meta:
        verbose_name = 'День события'
        verbose_name_plural = 'Дни события'
        ordering = ['date', 'start', 'pk']

    def __str__(self):
        return f'{self.landing} · {self.date:%d.%m.%Y}'


class EventLandingProgramRow(models.Model):
    day = models.ForeignKey(
        EventLandingDay,
        verbose_name='День',
        on_delete=models.CASCADE,
        related_name='rows',
    )
    start = models.TimeField('Начало')
    duration_min = models.PositiveSmallIntegerField('Длительность, мин')
    title = models.CharField('Заголовок', max_length=200)
    text = models.TextField('Описание', blank=True)
    is_break = models.BooleanField(
        'Перерыв',
        default=False,
        help_text='Перерыв/кофе-брейк — приглушённая строка.',
    )
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Строка программы'
        verbose_name_plural = 'Программа'
        ordering = ['order', 'start', 'pk']

    def __str__(self):
        return f'{self.start:%H:%M} {self.title}'


class EventLandingMaterial(models.Model):
    landing = models.ForeignKey(
        EventLanding,
        verbose_name='Лендинг',
        on_delete=models.CASCADE,
        related_name='materials',
    )
    title = models.CharField('Материал', max_length=200)
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Материал участника'
        verbose_name_plural = 'Материалы участника'
        ordering = ['order', 'pk']

    def __str__(self):
        return self.title


class EventLandingTile(models.Model):
    landing = models.ForeignKey(
        EventLanding,
        verbose_name='Лендинг',
        on_delete=models.CASCADE,
        related_name='tiles',
    )
    title = models.CharField('Заголовок', max_length=80)
    text = models.CharField('Текст', max_length=200, blank=True)
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Плитка «Для кого»'
        verbose_name_plural = 'Плитки «Для кого»'
        ordering = ['order', 'pk']

    def __str__(self):
        return self.title


class EventLandingGalleryImage(OrientedGalleryImage):
    """Фото события для карусели «О Space School». Пусто — фолбэк на галерею
    главной региона (во view)."""

    landing = models.ForeignKey(
        EventLanding,
        verbose_name='Лендинг',
        on_delete=models.CASCADE,
        related_name='gallery',
    )
    image = models.ImageField('Картинка', upload_to='eventlandings/gallery/')
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
    alt_text = models.CharField('Alt-текст', max_length=200, blank=True)

    class Meta(OrientedGalleryImage.Meta):
        verbose_name = 'Фото события'
        verbose_name_plural = 'Фото события'

    def __str__(self):
        return self.alt_text or f'Image #{self.pk}'
