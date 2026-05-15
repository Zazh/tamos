from django.db import models


# --- Глобальные справочники (одинаковые во всех регионах) -----------------

class Department(models.Model):
    """Отделение: «Русское» / «Казахское». Slug участвует в URL."""

    slug = models.SlugField('Slug (для URL)', max_length=20, unique=True)
    name = models.CharField('Название', max_length=80)
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Отделение'
        verbose_name_plural = 'Отделения'
        ordering = ['order', 'pk']

    def __str__(self):
        return self.name


class GradeGroup(models.Model):
    """Группа классов: «1 класс», «2–7 класс», «2–6 класс», «8–11 класс»,
    «7–11 класс». Slug участвует в URL (часть после префикса `grade-`)."""

    slug = models.SlugField('Slug (для URL, без префикса grade-)', max_length=20, unique=True)
    name = models.CharField(
        'Название',
        max_length=80,
        help_text='Полное название (для dropdown и breadcrumb).',
    )
    short_name = models.CharField(
        'Короткое название',
        max_length=40,
        blank=True,
        help_text='Для мобильной версии <380px (напр. «1 кл.»). Если пусто — '
                  'используется полное.',
    )
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Группа классов'
        verbose_name_plural = 'Группы классов'
        ordering = ['order', 'pk']

    def __str__(self):
        return self.name


# --- Per-region singleton с общими для страницы текстами -----------------

class AdmissionPage(models.Model):
    """Лендинг «Поступление» одного региона. Singleton (one-to-one с Region).
    Хранит тексты, общие для ВСЕХ вариантов (department × grade)."""

    region = models.OneToOneField(
        'regions.Region',
        verbose_name='Регион',
        on_delete=models.PROTECT,
        related_name='admission_page',
    )

    # --- Stepper (5 этапов в порядке DOM: 5 сверху → 1 снизу) ---
    # На десктопе: «Зачисление» сверху → «Консультация» снизу.
    # На мобиле: row-flex с reversed order, слева 1, справа 5.
    # active = пользователь по умолчанию на «Тестирование» (data-stage="1" в DOM = шаг 1).
    stage_consultation_title = models.CharField(
        'Stepper · Консультация · заголовок',
        max_length=80,
        help_text='Шаг 1 (мобайл слева, десктоп снизу). Напр. «Есть вопросы?».',
    )
    stage_consultation_meta = models.CharField(
        'Stepper · Консультация · подпись',
        max_length=120,
        blank=True,
    )
    stage_testing_title = models.CharField('Stepper · Тестирование · заголовок', max_length=80)
    stage_testing_meta = models.CharField('Stepper · Тестирование · подпись', max_length=120, blank=True)
    stage_result_title = models.CharField('Stepper · Результат · заголовок', max_length=80)
    stage_result_meta = models.CharField('Stepper · Результат · подпись', max_length=120, blank=True)
    stage_contract_title = models.CharField('Stepper · Договор · заголовок', max_length=80)
    stage_contract_meta = models.CharField('Stepper · Договор · подпись', max_length=120, blank=True)
    stage_enrollment_title = models.CharField('Stepper · Зачисление · заголовок', max_length=80)
    stage_enrollment_meta = models.CharField('Stepper · Зачисление · подпись', max_length=120, blank=True)

    # --- Section H3 заголовки (могут отличаться от stepper) ---
    testing_section_title = models.CharField(
        'Заголовок секции «Тестирование»',
        max_length=120,
        help_text='Над текстом этапа 01. Префикс «01 — » добавляется в шаблоне.',
    )
    result_section_title = models.CharField(
        'Заголовок секции «Результат»',
        max_length=120,
        help_text='Напр. «Результат тестирования» (длиннее, чем в stepper).',
    )
    contract_section_title = models.CharField('Заголовок секции «Договор и взнос»', max_length=120)
    enrollment_section_title = models.CharField('Заголовок секции «Зачисление»', max_length=120)
    consultation_section_title = models.CharField('Заголовок секции «Консультация»', max_length=120)

    # --- UI лейблы ---
    breadcrumb_root_label = models.CharField(
        'Breadcrumb · корень',
        max_length=80,
        default='Поступление',
    )
    department_dropdown_label = models.CharField(
        'Лейбл dropdown «Отделение»',
        max_length=80,
        default='Отделение:',
    )
    grade_dropdown_label = models.CharField(
        'Лейбл dropdown «Классы»',
        max_length=80,
        default='Классы:',
    )

    # --- Testing-rules + цена тестирования ---
    testing_rules_text = models.TextField(
        'Правила тестирования',
        help_text='Параграф под 4 карточками тестирования: про повторное, апелляции и т.д.',
    )
    testing_price_label = models.CharField(
        'Подпись цены тестирования',
        max_length=80,
        default='Стоимость тестирования',
    )
    testing_price_value = models.CharField(
        'Цена тестирования',
        max_length=40,
        help_text='Напр. «10 000 ₸».',
    )

    # --- Pricing-block (под прайс-картами этапа «Договор») ---
    enrollment_fee_text = models.TextField(
        'Текст про вступительный взнос',
        help_text='Под прайс-картами. HTML рендерится через |safe (поддержи '
                  '<span class="font-bold text-black">+ Вступительный взнос — N ₸</span> разово…).',
    )
    pricing_included_title = models.CharField(
        'Заголовок «Стоимость включает»',
        max_length=80,
        default='Стоимость включает',
    )
    pricing_excluded_title = models.CharField(
        'Заголовок «Не включено»',
        max_length=80,
        default='Не включено',
        blank=True,
    )

    # --- Enrollment + документы ---
    enrollment_lead = models.TextField(
        'Lead этапа «Зачисление»',
        help_text='Параграф над списком документов.',
    )
    documents_title = models.CharField(
        'Заголовок списка документов',
        max_length=120,
        default='Документы для зачисления',
    )

    # --- Consultation ---
    consultation_lead = models.TextField('Lead этапа «Консультация»')
    consultation_cta_text = models.CharField(
        'Текст CTA консультации',
        max_length=80,
        default='Записаться на консультацию',
    )

    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Лендинг «Поступление»'
        verbose_name_plural = 'Лендинги «Поступление»'

    def __str__(self):
        return f'Поступление — {self.region}'


class AdmissionIncludedItem(models.Model):
    """Пункт списка «Стоимость включает» / «Не включено». 1 inline на Page."""

    page = models.ForeignKey(
        AdmissionPage,
        verbose_name='Лендинг',
        on_delete=models.CASCADE,
        related_name='included_items',
    )
    text = models.CharField('Текст пункта', max_length=300)
    is_excluded = models.BooleanField(
        'Это «Не включено»?',
        default=False,
        help_text='Снимет ✓-иконку и подставит ✕. Иначе — обычный пункт «Стоимость включает».',
    )
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Пункт «Стоимость включает / не включено»'
        verbose_name_plural = 'Пункты «Стоимость включает / не включено»'
        ordering = ['is_excluded', 'order', 'pk']

    def __str__(self):
        prefix = '✕' if self.is_excluded else '✓'
        return f'{prefix} {self.text}'


class AdmissionDocument(models.Model):
    """Пункт списка «Документы для зачисления». Inline на Page."""

    page = models.ForeignKey(
        AdmissionPage,
        verbose_name='Лендинг',
        on_delete=models.CASCADE,
        related_name='documents',
    )
    text = models.CharField('Документ', max_length=300)
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Документ для зачисления'
        verbose_name_plural = 'Документы для зачисления'
        ordering = ['order', 'pk']

    def __str__(self):
        return self.text


# --- Per-combination (department × grade) -------------------------------

class AdmissionVariant(models.Model):
    """Конкретный вариант страницы: AdmissionPage × Department × GradeGroup.
    Например (Astana, Казахское, 1 класс). На регион ожидаем 6 вариантов:
    3 RU (1 / 2-7 / 8-11) + 3 KZ (1 / 2-6 / 7-11)."""

    page = models.ForeignKey(
        AdmissionPage,
        verbose_name='Лендинг',
        on_delete=models.CASCADE,
        related_name='variants',
    )
    department = models.ForeignKey(
        Department,
        verbose_name='Отделение',
        on_delete=models.PROTECT,
        related_name='variants',
    )
    grade = models.ForeignKey(
        GradeGroup,
        verbose_name='Группа классов',
        on_delete=models.PROTECT,
        related_name='variants',
    )

    # --- Hero ---
    h1 = models.CharField(
        'H1 страницы',
        max_length=200,
        help_text='Напр. «Поступление в 1 класс».',
    )
    hero_lead = models.TextField(
        'Lead под H1',
        blank=True,
        help_text='1–2 предложения о программе и отделении.',
    )

    # --- Testing (этап 01) ---
    testing_lead = models.TextField(
        'Lead этапа «Тестирование»',
        blank=True,
        help_text='Описание формата (20–60 минут, родитель присутствует, язык отделения).',
    )

    # --- Result (этап 02) ---
    result_intro = models.TextField(
        'Результат · вводный параграф',
        blank=True,
        help_text='Напр. «Решение приёмной комиссии сообщается родителям…».',
    )
    result_detail = models.TextField(
        'Результат · детали',
        blank=True,
        help_text='Что после положительного/отрицательного результата.',
    )

    # --- Contract (этап 03) ---
    pricing_lead = models.TextField(
        'Lead прайса',
        blank=True,
        help_text='Напр. «Стоимость обучения для 1 класса (русское отделение) на 2026–2027 учебный год…».',
    )

    class Meta:
        verbose_name = 'Вариант страницы'
        verbose_name_plural = 'Варианты страниц'
        unique_together = [('page', 'department', 'grade')]
        ordering = ['department__order', 'grade__order']

    def __str__(self):
        return f'{self.page.region} · {self.department} · {self.grade}'


class AdmissionTestingFeature(models.Model):
    """Карточка feature-card в этапе «Тестирование». 4 шт. в прототипе.
    Inline на Variant — содержание зависит от dept/grade."""

    variant = models.ForeignKey(
        AdmissionVariant,
        verbose_name='Вариант',
        on_delete=models.CASCADE,
        related_name='testing_features',
    )
    icon_svg = models.TextField(
        'SVG-иконка',
        blank=True,
        help_text='Полная разметка <svg>…</svg>. Менеджеру лучше не трогать; '
                  'правит разработчик. См. memory/admission.md по стилю.',
    )
    title = models.CharField('Заголовок карточки', max_length=120)
    description = models.TextField('Описание')
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Карточка «Тестирование»'
        verbose_name_plural = 'Карточки «Тестирование»'
        ordering = ['order', 'pk']

    def __str__(self):
        return self.title or f'TestingFeature #{self.pk}'


class AdmissionPricingPlan(models.Model):
    """Прайс-карта в этапе «Договор и взнос». 3 в прототипе (1 кл, ru, 2026–2027).
    Inline на Variant — цены меняются между классами и учебными годами."""

    class Highlight(models.TextChoices):
        BEST = 'best', 'Лучшая цена (gold-фон)'
        REGULAR = 'regular', 'Обычная (slate-фон)'

    # Tailwind не сканит Django-шаблоны — готовые классы хранятся здесь.
    BG_CSS = {
        'best': 'bg-gold/15',
        'regular': 'bg-slate-50',
    }

    variant = models.ForeignKey(
        AdmissionVariant,
        verbose_name='Вариант',
        on_delete=models.CASCADE,
        related_name='pricing_plans',
    )
    highlight = models.CharField(
        'Стиль карточки',
        max_length=20,
        choices=Highlight.choices,
        default=Highlight.REGULAR,
    )
    badge_text = models.CharField(
        'Текст баджа',
        max_length=80,
        blank=True,
        help_text='Напр. «Лучшая цена». Если пусто — место под бадж остаётся '
                  '(чтобы цены выравнивались по вертикали с соседями).',
    )
    icon_svg = models.TextField(
        'SVG-иконка',
        blank=True,
        help_text='Маленькая иконка слева сверху. <svg>…</svg>.',
    )
    label = models.CharField(
        'Подпись плана',
        max_length=120,
        help_text='Напр. «100% до 1 июня», «Ежеквартально», «Годовая оплата».',
    )
    price_value = models.CharField(
        'Цена (без валюты)',
        max_length=40,
        help_text='Напр. «4 086 000». Валюта — отдельным полем.',
    )
    price_currency = models.CharField('Валюта', max_length=10, default='₸')
    note = models.CharField(
        'Сноска под ценой',
        max_length=200,
        blank=True,
        help_text='Напр. «Полная оплата суммы до 1 июня», «Первый транш 1 395 000 ₸ до 1 июня».',
    )
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Прайс-карта'
        verbose_name_plural = 'Прайс-карты'
        ordering = ['order', 'pk']

    def __str__(self):
        return f'{self.label} · {self.price_value} {self.price_currency}'

    @property
    def bg_css(self) -> str:
        return self.BG_CSS.get(self.highlight, '')
