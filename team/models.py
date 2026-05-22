from django.db import models
from django.utils.html import strip_tags
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit

from .image_processors import FlattenAlphaToWhite


TEAM_IMAGE_QUALITY = 85
# Основное фото на /team/, /team/<slug>/ и в блоке featured на /program/.
# CSS-слот на detail.html lg:col-span-5 (~500px), 2× retina ≈ 1000, округлено.
TEAM_PHOTO_MAX_DIMENSION = 1024
# Маленькая аватарка для author-card в /blog/<slug>/ — CSS даёт 48×48,
# берём с запасом на retina (2×) и чуть выше.
TEAM_PHOTO_THUMB_DIMENSION = 256


class TeamMember(models.Model):
    """Член команды. Region-scoped: разный состав в каждом филиале.

    Превью карточки повторяет блок «Команда профессионалов» из
    spaceschool/pages/landing.html (photo + name + role + meta), но без
    цитаты на странице списка. Полная анкета (биография, резюме, LinkedIn)
    показывается на детальной странице.
    """

    region = models.ForeignKey(
        'regions.Region',
        verbose_name='Регион',
        on_delete=models.PROTECT,
        related_name='team_members',
    )

    slug = models.SlugField(
        'Slug',
        max_length=200,
        help_text='Сегмент в URL: aigerim-nurlanova. Уникален в пределах региона.',
    )
    name = models.CharField('Имя', max_length=120)
    role = models.CharField('Должность', max_length=160)
    meta = models.CharField(
        'Мета-строка',
        max_length=240,
        blank=True,
        help_text='Напр. «PhD в педагогике · 20 лет в международном образовании».',
    )
    quote = models.TextField(
        'Цитата',
        blank=True,
        help_text='Опционально. На странице списка не выводится; '
                  'показывается только на детальной.',
    )
    bio = models.TextField(
        'Биография',
        blank=True,
        help_text='Развёрнутое описание для детальной страницы. '
                  'HTML рендерится через |safe (h2/h3, p, ul/ol/li, blockquote).',
    )
    linkedin_url = models.URLField(
        'Ссылка на LinkedIn',
        blank=True,
        help_text='Полный URL профиля. Если указан — на детальной появится кнопка.',
    )

    photo = models.ImageField(
        'Фото',
        upload_to='team/photos/',
        blank=True,
        null=True,
    )
    photo_webp = ImageSpecField(
        source='photo',
        format='WEBP',
        options={'quality': TEAM_IMAGE_QUALITY},
        processors=[
            FlattenAlphaToWhite(),
            ResizeToFit(TEAM_PHOTO_MAX_DIMENSION, TEAM_PHOTO_MAX_DIMENSION, upscale=False),
        ],
    )
    # JPEG (а не «как исходник»): PNG-аватарки на 5–10× тяжелее, прозрачность
    # тут не нужна — отдаём плоский JPG.
    photo_compressed = ImageSpecField(
        source='photo',
        format='JPEG',
        options={'quality': TEAM_IMAGE_QUALITY, 'optimize': True, 'progressive': True},
        processors=[
            FlattenAlphaToWhite(),
            ResizeToFit(TEAM_PHOTO_MAX_DIMENSION, TEAM_PHOTO_MAX_DIMENSION, upscale=False),
        ],
    )
    photo_thumb_webp = ImageSpecField(
        source='photo',
        format='WEBP',
        options={'quality': TEAM_IMAGE_QUALITY},
        processors=[
            FlattenAlphaToWhite(),
            ResizeToFit(TEAM_PHOTO_THUMB_DIMENSION, TEAM_PHOTO_THUMB_DIMENSION, upscale=False),
        ],
    )
    photo_thumb_compressed = ImageSpecField(
        source='photo',
        format='JPEG',
        options={'quality': TEAM_IMAGE_QUALITY, 'optimize': True},
        processors=[
            FlattenAlphaToWhite(),
            ResizeToFit(TEAM_PHOTO_THUMB_DIMENSION, TEAM_PHOTO_THUMB_DIMENSION, upscale=False),
        ],
    )

    # Уровни преподавания — простой набор 1-4 / 5-8 / 9-11 (не M2M на справочник).
    # Учитель может вести в нескольких уровнях (например начальная + средняя).
    teaches_primary = models.BooleanField(
        'Младшие классы (1–4)',
        default=False,
        db_index=True,
    )
    teaches_middle = models.BooleanField(
        'Средние классы (5–8)',
        default=False,
        db_index=True,
    )
    teaches_senior = models.BooleanField(
        'Старшие классы (9–11)',
        default=False,
        db_index=True,
    )
    is_admin = models.BooleanField(
        'Администрация',
        default=False,
        db_index=True,
        help_text='Директор, координатор, куратор — отдельный chip на странице '
                  '/team/. Не зависит от teaches_*: учитель-завуч может быть и '
                  'преподавателем, и администрацией одновременно.',
    )

    order = models.PositiveSmallIntegerField('Порядок', default=0)
    is_published = models.BooleanField('Опубликован', default=True, db_index=True)
    is_featured = models.BooleanField(
        'Избранный (на лендинге программы)',
        default=False,
        db_index=True,
        help_text='Если включено — попадает в блок «Команда профессионалов» '
                  'на странице «Программа» текущего региона. Порядок '
                  'наследуется из поля «Порядок».',
    )
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    seo_title = models.CharField(
        'SEO title (<title>)',
        max_length=80,
        blank=True,
        help_text='50–60 символов. Если пусто — fallback на «ФИО — Должность».',
    )
    seo_description = models.CharField(
        'SEO description (meta)',
        max_length=200,
        blank=True,
        help_text='150–160 символов. Если пусто — fallback на начало '
                  'биографии или мета-строку.',
    )
    og_title = models.CharField(
        'OG title',
        max_length=80,
        blank=True,
        help_text='Если пусто — fallback на seo_title → «ФИО — Должность».',
    )
    og_description = models.CharField(
        'OG description',
        max_length=300,
        blank=True,
        help_text='Если пусто — fallback на seo_description → начало биографии.',
    )

    class Meta:
        verbose_name = 'Член команды'
        verbose_name_plural = 'Команда'
        ordering = ['order', 'pk']
        constraints = [
            models.UniqueConstraint(
                fields=['region', 'slug'],
                name='team_member_region_slug_unique',
            ),
        ]

    def __str__(self):
        return self.name or f'TeamMember #{self.pk}'

    @property
    def bio_plain(self) -> str:
        """Биография без HTML-тегов — для SEO/OG description fallback."""
        if not self.bio:
            return ''
        return strip_tags(self.bio).replace('\xa0', ' ').strip()

    @property
    def effective_seo_title(self) -> str:
        if self.seo_title:
            return self.seo_title
        parts = [p for p in (self.name, self.role) if p]
        return ' — '.join(parts)

    @property
    def effective_seo_description(self) -> str:
        if self.seo_description:
            return self.seo_description
        return self.bio_plain or self.meta or ''

    @property
    def effective_og_title(self) -> str:
        return self.og_title or self.effective_seo_title

    @property
    def effective_og_description(self) -> str:
        return self.og_description or self.effective_seo_description
