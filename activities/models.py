from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _


def default_all_classes():
    """Дефолт ArrayField для ActivityGroup.classes — «все классы 1–11».

    Пустой массив трактуется как «не задано» и не должен оставаться в БД
    (см. миграцию 0004). Callable, чтобы Django не шарил один список
    между записями (mutable default).
    """
    return list(range(1, 12))


def format_classes_range(classes, lang=None):
    """Собирает строку диапазона классов на конкретном языке.

    Примеры:
        [1, 2, 3, 4]    → ru «1–4 класс» / kk «1–4 сынып» / en «Grades 1–4»
        [5]             → ru «5 класс» / kk «5 сынып» / en «Grade 5»
        []              → ''
    """
    if not classes:
        return ''
    if lang is None:
        lang = get_language() or 'ru'
    lang = (lang or 'ru')[:2]
    if lang not in ('ru', 'kk', 'en'):
        lang = 'ru'

    lo, hi = min(classes), max(classes)

    if lang == 'en':
        return f'Grade {lo}' if lo == hi else f'Grades {lo}–{hi}'

    unit = 'сынып' if lang == 'kk' else 'класс'
    return f'{lo} {unit}' if lo == hi else f'{lo}–{hi} {unit}'


class ActivitySection(models.Model):
    """Глобальная категория-секция кружков (Спортивные / Творческие / Академические)."""

    # Tailwind не сканит Django-шаблоны — поэтому полные классы хранятся
    # в карте, шаблон использует только готовые строки. Цвета совпадают
    # с теми, что уже встречаются в spaceschool/pages/landing.html, поэтому
    # final CSS их уже содержит.
    BADGE_CSS = {
        'sports': 'bg-orange-400/10 text-orange-500',
        'creative': 'bg-indigo-400/10 text-indigo-500',
        'academic': 'bg-green-600/10 text-green-600',
    }

    slug = models.SlugField(
        'Slug',
        unique=True,
        max_length=40,
        help_text='Машинное имя: sports / creative / academic.',
    )
    title = models.CharField('Название', max_length=80)
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Секция активностей'
        verbose_name_plural = 'Секции активностей'
        ordering = ['order', 'slug']

    def __str__(self):
        return self.title or self.slug

    @property
    def badge_css(self) -> str:
        return self.BADGE_CSS.get(self.slug, 'bg-gray-400/10 text-gray-500')


class Activity(models.Model):
    """Кружок (одна строчка-аккордеон).

    `class_range` подзаголовка в шапке аккордеона нет в полях — он считается
    автоматически (`class_range_display`) из объединения classes всех групп.

    Тренер хранится на УРОВНЕ ГРУППЫ (см. `ActivityGroup.teacher_*`) — в
    разных группах одного кружка могут быть разные тренера.
    """

    region = models.ForeignKey(
        'regions.Region',
        verbose_name='Регион',
        on_delete=models.PROTECT,
        related_name='activities',
    )
    section = models.ForeignKey(
        ActivitySection,
        verbose_name='Секция',
        on_delete=models.PROTECT,
        related_name='activities',
    )
    name = models.CharField('Название', max_length=60)
    description = models.TextField('Описание', blank=True)
    location = models.CharField(
        'Локация',
        max_length=120,
        blank=True,
        help_text='Где проходят занятия (общее для всех групп кружка).',
    )
    is_published = models.BooleanField('Опубликован', default=True)
    is_featured = models.BooleanField(
        'Избранный',
        default=False,
        db_index=True,
        help_text='Показывать в секции «Внеклассные» на странице программы.',
    )
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Кружок'
        verbose_name_plural = 'Кружки'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name or f'Activity #{self.pk}'

    @property
    def class_range_display(self) -> str:
        """Авто-сборка диапазона классов из всех групп.

        Берёт объединение `classes` всех групп, считает min/max,
        форматирует под текущий язык.
        """
        all_classes = []
        for g in self.groups.all():
            all_classes.extend(g.classes or [])
        return format_classes_range(all_classes)

    @property
    def days_display(self) -> str:
        """Сводка дней по всем группам через bullet.

        Если у всех групп одинаковые дни — одна строка («Пн-Ср-Пт»).
        Если разные — через « • » («Пн-Пт • Пн-Ср • Ср-Пт»). Дубликаты
        удалены; порядок групп сохраняется.
        """
        seen = []
        for g in self.groups.all():
            d = g.days_short_display
            if d and d not in seen:
                seen.append(d)
        return ' • '.join(seen)


class ActivityGroup(models.Model):
    """Группа внутри кружка. Своё расписание, цена, лимит учеников, статус набора."""

    class StudentsStatus(models.TextChoices):
        RECRUITING = 'recruiting', _('Идёт набор')
        HAS_PLACES = 'has_places', _('Есть свободные места')
        FULL = 'full', _('Заполнено')

    STATUS_CSS = {
        'recruiting': 'text-emerald-600',
        'has_places': 'text-amber-500',
        'full': 'text-red-500',
    }

    activity = models.ForeignKey(
        Activity,
        verbose_name='Кружок',
        on_delete=models.CASCADE,
        related_name='groups',
    )
    label = models.CharField(
        'Название группы',
        max_length=120,
        blank=True,
        help_text='Опциональное название (напр. «Младшие», «Продвинутые»). Если пусто — '
                  'подставляется авто-диапазон из `classes`.',
    )
    teacher_name = models.CharField(
        'Тренер — имя',
        max_length=120,
        blank=True,
        help_text='Имя ведущего тренера этой группы. У разных групп одного кружка '
                  'могут быть разные тренера.',
    )
    teacher_phone = models.CharField(
        'Тренер — телефон (E.164)',
        max_length=20,
        blank=True,
        help_text='Нормализованный +77051234567. В UI публичной страницы пока не показывается.',
    )
    teacher_bio = models.TextField(
        'Тренер — био',
        blank=True,
        help_text='1–2 предложения про тренера. Опционально.',
    )
    classes = ArrayField(
        models.PositiveSmallIntegerField(),
        verbose_name='Классы',
        default=default_all_classes,
        blank=True,
        size=11,
        help_text='Список классов, в которых занимаются — напр. [3, 4, 5, 6]. '
                  'По умолчанию — все классы 1–11. Min/max и текст в шапке '
                  'аккордеона считаются автоматически.',
    )
    price = models.PositiveIntegerField(
        'Стоимость, ₸/мес',
        null=True,
        blank=True,
        help_text='Целое число тенге за месяц. Пусто — цена не указана.',
    )
    students_status = models.CharField(
        'Статус набора',
        max_length=20,
        choices=StudentsStatus.choices,
        default=StudentsStatus.RECRUITING,
    )
    min_students = models.PositiveSmallIntegerField('Минимум учеников', default=5)
    max_students = models.PositiveSmallIntegerField('Максимум учеников', default=20)
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        ordering = ['order', 'pk']

    def __str__(self):
        return self.label_display or f'Group #{self.pk}'

    @property
    def classes_min(self) -> int | None:
        return min(self.classes) if self.classes else None

    @property
    def classes_max(self) -> int | None:
        return max(self.classes) if self.classes else None

    @property
    def label_display(self) -> str:
        """Ручной `label` (если задан на текущем языке) или авто-диапазон.

        Если на текущем языке перевода нет и classes пуст — fallback на
        `label_ru`, чтобы карточка не оставалась без заголовка.
        """
        lang = (get_language() or 'ru')[:2]
        if lang not in ('ru', 'kk', 'en'):
            lang = 'ru'
        manual = (getattr(self, f'label_{lang}', '') or '').strip()
        if manual:
            return manual
        auto = format_classes_range(self.classes, lang)
        if auto:
            return auto
        return (self.label_ru or '').strip()

    @property
    def students_status_css(self) -> str:
        return self.STATUS_CSS.get(self.students_status, 'text-black/60')

    @property
    def price_display(self) -> str:
        if self.price is None:
            return ''
        return f'{self.price:,} ₸'.replace(',', ' ')

    @property
    def students_text(self) -> str:
        """Текст лимита учеников в шапке карточки.

        Использует `gettext_lazy` через `_` — Django разрешит строку на текущем
        активном языке (URL `/<lang>/...` устанавливает active language).
        """
        if self.students_status == self.StudentsStatus.FULL and self.max_students:
            return _('До %(n)d учеников') % {'n': self.max_students}
        if self.students_status == self.StudentsStatus.HAS_PLACES:
            if self.min_students and self.max_students:
                return _('%(lo)d–%(hi)d учеников') % {
                    'lo': self.min_students, 'hi': self.max_students,
                }
            if self.max_students:
                return _('До %(n)d учеников') % {'n': self.max_students}
        if self.min_students:
            return _('От %(n)d учеников') % {'n': self.min_students}
        return ''

    @property
    def days_csv(self) -> str:
        """Уникальные дни недели группы через запятую: 'mon,wed,fri'.

        Используется на карточке как data-атрибут для клиентского фильтра
        по дню недели.
        """
        days = sorted(
            {s.day for s in self.schedule_slots.all()},
            key=lambda d: ScheduleSlot.DAY_ORDER.get(d, 99),
        )
        return ','.join(days)

    @property
    def days_short_display(self) -> str:
        """Дни недели через тире: «Пн-Ср-Пт» / «Mon-Wed-Fri» / «Дс-Ср-Жм».

        Локализуется через DAY_SHORT (lazy gettext).
        """
        days = sorted(
            {s.day for s in self.schedule_slots.all()},
            key=lambda d: ScheduleSlot.DAY_ORDER.get(d, 99),
        )
        return '-'.join(str(ScheduleSlot.DAY_SHORT.get(d, d)) for d in days)

    @property
    def schedule_display(self) -> str:
        slots = sorted(
            self.schedule_slots.all(),
            key=lambda s: (ScheduleSlot.DAY_ORDER.get(s.day, 99), s.start_time),
        )
        if not slots:
            return ''

        groups = []
        current_time = None
        current_days = []
        for s in slots:
            key = (s.start_time, s.end_time)
            if key == current_time:
                current_days.append(str(s.day_short))
            else:
                if current_days:
                    groups.append((current_time, current_days))
                current_time = key
                current_days = [str(s.day_short)]
        if current_days:
            groups.append((current_time, current_days))

        def fmt(start, end, days):
            time_str = f'{start:%H:%M}–{end:%H:%M}'
            return f'{", ".join(days)} · {time_str}'

        if len(groups) == 1:
            (start, end), days = groups[0]
            return fmt(start, end, days)
        return '; '.join(fmt(start, end, days) for (start, end), days in groups)


class ScheduleSlot(models.Model):
    """Один слот расписания группы: день + время начала/окончания."""

    class Day(models.TextChoices):
        MON = 'mon', _('Понедельник')
        TUE = 'tue', _('Вторник')
        WED = 'wed', _('Среда')
        THU = 'thu', _('Четверг')
        FRI = 'fri', _('Пятница')
        SAT = 'sat', _('Суббота')
        SUN = 'sun', _('Воскресенье')

    DAY_SHORT = {
        'mon': _('Пн'),
        'tue': _('Вт'),
        'wed': _('Ср'),
        'thu': _('Чт'),
        'fri': _('Пт'),
        'sat': _('Сб'),
        'sun': _('Вс'),
    }

    DAY_ORDER = {'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6}

    group = models.ForeignKey(
        ActivityGroup,
        verbose_name='Группа',
        on_delete=models.CASCADE,
        related_name='schedule_slots',
    )
    day = models.CharField('День недели', max_length=3, choices=Day.choices)
    start_time = models.TimeField('Начало')
    end_time = models.TimeField('Окончание')
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Слот расписания'
        verbose_name_plural = 'Слоты расписания'
        ordering = ['order', 'pk']

    def __str__(self):
        return f'{self.day} {self.start_time:%H:%M}–{self.end_time:%H:%M}'

    @property
    def day_short(self):
        return self.DAY_SHORT.get(self.day, self.day)
