from django.db import models
from imagekit.models import ImageSpecField


# Лендинг «Программа». Singleton per region (как HomePage/ContactsPage).
# Большая часть текстов — на самой ProgramPage (Hero, заголовки секций).
# Списочные секции (карточки, члены команды, FAQ-пункты и т.д.) — inline-модели.
PROGRAM_IMAGE_QUALITY = 85


class ProgramPage(models.Model):
    """Лендинг «Программа» для одного региона."""

    region = models.OneToOneField(
        'regions.Region',
        verbose_name='Регион',
        on_delete=models.PROTECT,
        related_name='program_page',
    )

    # --- Hero (без фоновой картинки — там декоративное видео-планета в шаблоне) ---
    hero_badge_text = models.CharField(
        'Бадж над заголовком',
        max_length=120,
        help_text='Маленький ярлычок над h1 (напр. «Международная школа в Астане»).',
    )
    hero_title = models.TextField(
        'Заголовок hero (h1)',
        help_text='HTML-разметка (рендерится через |safe). Используй '
                  '<span class="hero-fit">…</span> для построчной подгонки '
                  'шрифта на мобиле; внутри можно <span class="hero-break">…</span> '
                  '(десктопный перенос) и <span class="text-gold">…</span> для акцента. '
                  'Пример: <span class="hero-fit">Школа для детей</span>'
                  '<span class="hero-fit">которые <span class="hero-break">поступят</span></span>'
                  '<span class="hero-fit">в <span class="text-gold">TOP-100</span> вузов</span>',
    )
    hero_subtitle = models.TextField('Подзаголовок hero (h2)')
    hero_cta_primary_text = models.CharField('Текст основной CTA', max_length=80)
    hero_cta_secondary_text = models.CharField('Текст вторичной CTA', max_length=80)

    # --- Section «Кому подходит» (audience) ---
    audience_label = models.CharField('Лейбл секции «Кому подходит»', max_length=80)
    audience_title = models.TextField(
        'Заголовок секции «Кому подходит»',
        help_text='Перенос строки = <br>.',
    )
    audience_subtitle = models.TextField('Подзаголовок секции «Кому подходит»', blank=True)
    audience_photo_woman = models.ImageField(
        'Фото слева (круглое, девушка)',
        upload_to='programs/audience/',
        blank=True,
        null=True,
    )
    audience_photo_woman_webp = ImageSpecField(
        source='audience_photo_woman',
        format='WEBP',
        options={'quality': PROGRAM_IMAGE_QUALITY},
    )
    audience_photo_woman_compressed = ImageSpecField(
        source='audience_photo_woman',
        options={'quality': PROGRAM_IMAGE_QUALITY, 'optimize': True},
    )
    audience_photo_library = models.ImageField(
        'Фото справа (прямоугольное, библиотека)',
        upload_to='programs/audience/',
        blank=True,
        null=True,
    )
    audience_photo_library_webp = ImageSpecField(
        source='audience_photo_library',
        format='WEBP',
        options={'quality': PROGRAM_IMAGE_QUALITY},
    )
    audience_photo_library_compressed = ImageSpecField(
        source='audience_photo_library',
        options={'quality': PROGRAM_IMAGE_QUALITY, 'optimize': True},
    )

    # --- Section «Что получает» (benefits / results) ---
    benefits_label = models.CharField('Лейбл секции «Что получает»', max_length=80)
    benefits_title = models.TextField('Заголовок секции «Что получает»')
    benefits_subtitle = models.TextField('Подзаголовок секции «Что получает»', blank=True)
    benefits_photo_kid = models.ImageField(
        'Фото справа (ученик)',
        upload_to='programs/benefits/',
        blank=True,
        null=True,
    )
    benefits_photo_kid_webp = ImageSpecField(
        source='benefits_photo_kid',
        format='WEBP',
        options={'quality': PROGRAM_IMAGE_QUALITY},
    )
    benefits_photo_kid_compressed = ImageSpecField(
        source='benefits_photo_kid',
        options={'quality': PROGRAM_IMAGE_QUALITY, 'optimize': True},
    )

    # --- Section «Программы» (две карточки: Начальная / Старшая) ---
    programs_label = models.CharField('Лейбл секции «Программы»', max_length=80)
    programs_title = models.TextField('Заголовок секции «Программы»')
    programs_subtitle = models.TextField('Подзаголовок секции «Программы»', blank=True)
    programs_cta_text = models.CharField('Текст CTA в секции «Программы»', max_length=80, blank=True)

    # --- Section «Команда» (team) ---
    team_label = models.CharField('Лейбл секции «Команда»', max_length=80)
    team_title = models.TextField('Заголовок секции «Команда»')
    team_subtitle = models.TextField('Подзаголовок секции «Команда»', blank=True)

    # --- Section «Аттестат» (certificate) ---
    certificate_label = models.CharField('Лейбл секции «Аттестат»', max_length=80)
    certificate_title = models.TextField('Заголовок секции «Аттестат»')
    certificate_subtitle = models.TextField('Подзаголовок секции «Аттестат»', blank=True)
    certificate_preview_image = models.ImageField(
        'Образец сертификата',
        upload_to='programs/certificate/',
        blank=True,
        null=True,
    )
    certificate_preview_image_webp = ImageSpecField(
        source='certificate_preview_image',
        format='WEBP',
        options={'quality': PROGRAM_IMAGE_QUALITY},
    )
    certificate_preview_image_compressed = ImageSpecField(
        source='certificate_preview_image',
        options={'quality': PROGRAM_IMAGE_QUALITY, 'optimize': True},
    )
    certificate_cta_text = models.CharField('Текст CTA «Посмотреть сертификат»', max_length=120, blank=True)

    # --- Section «Внеклассные занятия» (activities) ---
    activities_label = models.CharField('Лейбл секции «Внеклассные»', max_length=80)
    activities_title = models.TextField('Заголовок секции «Внеклассные»')
    activities_subtitle = models.TextField('Подзаголовок секции «Внеклассные»', blank=True)
    activities_cta_text = models.CharField('Текст CTA «Смотреть все активности»', max_length=120, blank=True)

    # --- Section «В цифрах» (stats / about) ---
    stats_label = models.CharField('Лейбл секции «В цифрах»', max_length=80)
    stats_title = models.TextField('Заголовок секции «В цифрах»')
    stats_intro_text = models.TextField('Вводный текст секции «В цифрах»', blank=True)
    stats_photo = models.ImageField(
        'Фото школы (справа от цифр)',
        upload_to='programs/stats/',
        blank=True,
        null=True,
    )
    stats_photo_webp = ImageSpecField(
        source='stats_photo',
        format='WEBP',
        options={'quality': PROGRAM_IMAGE_QUALITY},
    )
    stats_photo_compressed = ImageSpecField(
        source='stats_photo',
        options={'quality': PROGRAM_IMAGE_QUALITY, 'optimize': True},
    )

    # --- Section FAQ ---
    faq_label = models.CharField('Лейбл секции «FAQ»', max_length=80)
    faq_title = models.TextField('Заголовок секции «FAQ»')

    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Лендинг «Программа»'
        verbose_name_plural = 'Лендинги «Программа»'

    def __str__(self):
        return f'Программа — {self.region}'


class ProgramAudienceItem(models.Model):
    """Карточка в секции «Кому подходит». 4 шт. в прототипе."""

    program_page = models.ForeignKey(
        ProgramPage,
        verbose_name='Лендинг',
        on_delete=models.CASCADE,
        related_name='audience_items',
    )
    icon_svg = models.TextField(
        'SVG-иконка',
        blank=True,
        help_text='Полная разметка <svg>…</svg>. Если пусто — место под иконкой остаётся, '
                  'но иконка не отрисуется. Менеджеру лучше не трогать; иконки правит разработчик.',
    )
    title = models.CharField('Заголовок карточки', max_length=200)
    description = models.TextField('Описание')
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Карточка «Кому подходит»'
        verbose_name_plural = 'Карточки «Кому подходит»'
        ordering = ['order', 'pk']

    def __str__(self):
        return self.title or f'Audience #{self.pk}'


class ProgramBenefitItem(models.Model):
    """Карточка в секции «Что получает». 4 шт. с автонумерацией 1/2/3/4 по order."""

    program_page = models.ForeignKey(
        ProgramPage,
        verbose_name='Лендинг',
        on_delete=models.CASCADE,
        related_name='benefit_items',
    )
    title = models.CharField('Заголовок карточки', max_length=200)
    description = models.TextField('Описание')
    order = models.PositiveSmallIntegerField(
        'Порядок',
        default=0,
        help_text='Номер карточки в секции рендерится автоматически по позиции.',
    )

    class Meta:
        verbose_name = 'Карточка «Что получает»'
        verbose_name_plural = 'Карточки «Что получает»'
        ordering = ['order', 'pk']

    def __str__(self):
        return self.title or f'Benefit #{self.pk}'


class ProgramVariantCard(models.Model):
    """Большая карточка программы (Начальная / Средняя+старшая). 2 шт. в прототипе."""

    class BadgeStyle(models.TextChoices):
        GOLD = 'gold', 'Золотой (начальная)'
        SECONDARY = 'secondary', 'Синий (старшая)'

    # Tailwind не сканит Django-шаблоны: динамические классы вида
    # `bg-{{ style }}` не попадут в финальный CSS. Поэтому таблица пар
    # (style → готовые классы) живёт здесь, и в шаблоне просто рендерится
    # `{{ card.badge_css }}`.
    BADGE_CSS = {
        'gold':      'bg-gold text-black',
        'secondary': 'bg-secondary text-white',
    }
    ACCENT_CSS = {
        'gold':      'text-gold',
        'secondary': 'text-secondary',
    }
    ARROW_FILL = {
        'gold':      '#111111',
        'secondary': '#fff',
    }

    program_page = models.ForeignKey(
        ProgramPage,
        verbose_name='Лендинг',
        on_delete=models.CASCADE,
        related_name='variant_cards',
    )
    badge_text = models.CharField(
        'Бадж карточки',
        max_length=60,
        help_text='Напр. «1–4 класс».',
    )
    badge_style = models.CharField(
        'Стиль баджа и акцента',
        max_length=20,
        choices=BadgeStyle.choices,
        default=BadgeStyle.GOLD,
        help_text='Цвет баджа и стрелки в углу карточки.',
    )
    title = models.CharField('Заголовок карточки', max_length=120)
    tags = models.TextField(
        'Тэги-бейджи',
        blank=True,
        help_text='Каждая строка = один маленький бейдж (напр. «Cambridge Primary»).',
    )
    features = models.TextField(
        'Список фич с галочкой',
        blank=True,
        help_text='Каждая строка = один пункт списка.',
    )
    footer_label = models.CharField(
        'Метка футера карточки',
        max_length=80,
        blank=True,
        help_text='Напр. «Выпускник получает:».',
    )
    footer_value = models.CharField(
        'Значение футера',
        max_length=120,
        blank=True,
        help_text='Напр. «Cambridge Primary Certificate».',
    )
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Карточка программы'
        verbose_name_plural = 'Карточки программ'
        ordering = ['order', 'pk']

    def __str__(self):
        return self.title or f'Variant #{self.pk}'

    @property
    def tag_lines(self) -> list[str]:
        return [line.strip() for line in self.tags.splitlines() if line.strip()]

    @property
    def feature_lines(self) -> list[str]:
        return [line.strip() for line in self.features.splitlines() if line.strip()]

    @property
    def badge_css(self) -> str:
        return self.BADGE_CSS.get(self.badge_style, '')

    @property
    def accent_css(self) -> str:
        return self.ACCENT_CSS.get(self.badge_style, '')

    @property
    def arrow_fill(self) -> str:
        return self.ARROW_FILL.get(self.badge_style, '#fff')


class ProgramTeamMember(models.Model):
    """Член команды в слайдере «Команда профессионалов»."""

    program_page = models.ForeignKey(
        ProgramPage,
        verbose_name='Лендинг',
        on_delete=models.CASCADE,
        related_name='team_members',
    )
    photo = models.ImageField(
        'Фото',
        upload_to='programs/team/',
        blank=True,
        null=True,
    )
    photo_webp = ImageSpecField(
        source='photo',
        format='WEBP',
        options={'quality': PROGRAM_IMAGE_QUALITY},
    )
    photo_compressed = ImageSpecField(
        source='photo',
        options={'quality': PROGRAM_IMAGE_QUALITY, 'optimize': True},
    )
    name = models.CharField('Имя', max_length=120)
    role = models.CharField('Должность', max_length=120)
    meta = models.CharField(
        'Мета-строка',
        max_length=200,
        blank=True,
        help_text='Напр. «PhD в педагогике · 20 лет в международном образовании».',
    )
    quote = models.TextField('Цитата', blank=True)
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Член команды'
        verbose_name_plural = 'Члены команды'
        ordering = ['order', 'pk']

    def __str__(self):
        return self.name or f'Team #{self.pk}'


class ProgramCertificateFeature(models.Model):
    """Карточка-фича в секции «Аттестат» (glass-card 4 шт.)."""

    program_page = models.ForeignKey(
        ProgramPage,
        verbose_name='Лендинг',
        on_delete=models.CASCADE,
        related_name='certificate_features',
    )
    icon_svg = models.TextField(
        'SVG-иконка',
        blank=True,
        help_text='Полная разметка <svg>…</svg>.',
    )
    title = models.CharField('Заголовок карточки', max_length=200)
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Карточка «Аттестат»'
        verbose_name_plural = 'Карточки «Аттестат»'
        ordering = ['order', 'pk']

    def __str__(self):
        return self.title or f'CertFeature #{self.pk}'


class ProgramActivityItem(models.Model):
    """Пункт в accordion «Внеклассные занятия»."""

    class CategoryColor(models.TextChoices):
        INDIGO = 'indigo', 'Индиго (Технологии)'
        RED = 'red', 'Красный (Наука)'
        GREEN = 'green', 'Зелёный (Риторика)'
        ORANGE = 'orange', 'Оранжевый (Спорт)'

    class StudentsStatus(models.TextChoices):
        RECRUITING = 'recruiting', 'Идёт набор'
        FULL = 'full', 'Мест нет'

    # Tailwind 4 не сканит Django-шаблоны — поэтому хранится готовый класс,
    # а не имя цвета. Если понадобится новый цвет: добавить пару в choices,
    # подобрать оттенки и заодно использовать класс хотя бы раз в
    # `spaceschool/pages/`, чтобы Tailwind их сгенерил.
    CATEGORY_CSS = {
        'indigo': 'bg-indigo-400/10 text-indigo-500',
        'red':    'bg-red-400/10 text-red-400',
        'green':  'bg-green-600/10 text-green-600',
        'orange': 'bg-orange-400/10 text-orange-400',
    }

    STATUS_CSS = {
        'recruiting': 'text-emerald-600',
        'full':       'text-red-500',
    }

    program_page = models.ForeignKey(
        ProgramPage,
        verbose_name='Лендинг',
        on_delete=models.CASCADE,
        related_name='activity_items',
    )
    time_label = models.CharField(
        'Время (устаревшее, не используется)',
        max_length=60,
        blank=True,
        help_text='Старое поле, оставлено для совместимости. Расписание теперь в «schedule».',
    )
    title = models.CharField('Название', max_length=200)
    class_range = models.CharField(
        'Классы',
        max_length=60,
        blank=True,
        help_text='Подзаголовок в шапке (напр. «1–5 класс»).',
    )
    category = models.CharField(
        'Категория',
        max_length=60,
        blank=True,
        help_text='Бейдж справа от стрелки (напр. «Технологии»).',
    )
    category_color = models.CharField(
        'Цвет категории',
        max_length=20,
        choices=CategoryColor.choices,
        default=CategoryColor.INDIGO,
    )
    description = models.TextField('Описание (вверху раскрытого блока)', blank=True)
    # Группа (1 на активность на лендинге программы)
    group_title = models.CharField(
        'Название группы',
        max_length=120,
        blank=True,
        help_text='Заголовок карточки-группы (напр. «Основная группа» или «1–5 класс»).',
    )
    schedule = models.CharField(
        'Расписание',
        max_length=120,
        blank=True,
        help_text='Напр. «Пн, Ср · 14:00–15:30».',
    )
    students_text = models.CharField(
        'Учащихся (текст)',
        max_length=80,
        blank=True,
        help_text='Напр. «От 5 учеников» или «До 10 учеников».',
    )
    students_status = models.CharField(
        'Статус набора',
        max_length=20,
        choices=StudentsStatus.choices,
        blank=True,
        help_text='Цветной хвостик после количества учеников.',
    )
    location = models.CharField('Локация', max_length=120, blank=True)
    price = models.CharField(
        'Стоимость',
        max_length=60,
        blank=True,
        help_text='Напр. «25 000 ₸/мес».',
    )
    trainer_name = models.CharField('ФИО тренера', max_length=200, blank=True)
    trainer_bio = models.TextField('Био тренера', blank=True)
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Активность'
        verbose_name_plural = 'Активности'
        ordering = ['order', 'pk']

    def __str__(self):
        return self.title or f'Activity #{self.pk}'

    @property
    def category_badge_css(self) -> str:
        return self.CATEGORY_CSS.get(self.category_color, 'bg-gray-400/10 text-gray-500')

    @property
    def students_status_css(self) -> str:
        return self.STATUS_CSS.get(self.students_status, '')

    @property
    def has_group_card(self) -> bool:
        """Показывать ли карточку-группу в раскрытом аккордеоне."""
        return bool(self.group_title or self.schedule or self.students_text
                    or self.location or self.price or self.trainer_name)


class ProgramStat(models.Model):
    """Цифра в секции «Space School в цифрах»."""

    program_page = models.ForeignKey(
        ProgramPage,
        verbose_name='Лендинг',
        on_delete=models.CASCADE,
        related_name='stats',
    )
    value = models.CharField(
        'Значение',
        max_length=20,
        help_text='Напр. «94%», «3», «100%».',
    )
    label = models.CharField(
        'Подпись',
        max_length=120,
        help_text='Перенос строки можно добавить через <br> (HTML экранируется — '
                  'для переноса используется CSS, текст вводи одной строкой).',
    )
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Цифра'
        verbose_name_plural = 'Цифры'
        ordering = ['order', 'pk']

    def __str__(self):
        return f'{self.value} — {self.label}' if self.value else f'Stat #{self.pk}'


class ProgramFaqItem(models.Model):
    """Пара «вопрос-ответ» в FAQ."""

    program_page = models.ForeignKey(
        ProgramPage,
        verbose_name='Лендинг',
        on_delete=models.CASCADE,
        related_name='faq_items',
    )
    question = models.CharField('Вопрос', max_length=255)
    answer = models.TextField('Ответ')
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Вопрос FAQ'
        verbose_name_plural = 'Вопросы FAQ'
        ordering = ['order', 'pk']

    def __str__(self):
        return self.question or f'FAQ #{self.pk}'
