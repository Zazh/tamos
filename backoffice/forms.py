from django import forms
from django.conf import settings
from django.contrib.auth import authenticate
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _

from feedback.models import Lead
from pages.models import (
    ContactsDepartment,
    ContactsPage,
    HomePage,
)
from programs.models import (
    ProgramAudienceItem,
    ProgramBenefitItem,
    ProgramCertificateFeature,
    ProgramFaqItem,
    ProgramPage,
    ProgramStat,
    ProgramTeamMember,
    ProgramVariantCard,
)


# Языки modeltranslation для backoffice-форм. Источник правды — settings.
TRANSLATION_LANGS = settings.MODELTRANSLATION_LANGUAGES  # ('ru', 'kk', 'en')


def _localized(*field_names):
    """Развернуть `('hero_title',)` в `('hero_title_ru', 'hero_title_kk', 'hero_title_en')`.

    Используется в Meta.fields для ModelForm на translatable моделях. Базовое
    (untranslated) поле не включаем — modeltranslation хранит данные в `_<lang>`
    колонках, а base используется только при чтении (резолвится по active language).
    """
    return tuple(f'{name}_{lang}' for name in field_names for lang in TRANSLATION_LANGS)


def _strip_lang(name):
    """`hero_title_ru` → `hero_title`. Для не-локализованных полей — без изменений."""
    for lang in TRANSLATION_LANGS:
        suffix = f'_{lang}'
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def _apply_backoffice_widget_classes(form, *, html_fields=(), compact_fields=()):
    """Прокинуть нужный bo-class на каждый widget формы — чтобы шаблон не
    рендерил input'ы вручную, а просто ставил `{{ form.field }}` где надо.

    Также для translatable полей расставляет placeholder с подсказкой
    fallback на ru.

    Параметры:
      html_fields — base-имена textarea-полей с HTML-разметкой (rows=4 моноспейс).
      compact_fields — base-имена textarea-полей, которые визуально должны быть
        однострочными (заголовки/подзаголовки секций — TextField в модели только
        ради совместимости со старым content'ом, в UI это короткие однострочники).
        rows=1, без auto-resize вверх.
    """
    for name, field in form.fields.items():
        widget = field.widget
        attrs = widget.attrs
        base_name = _strip_lang(name)
        is_translation = base_name != name
        lang = name.split('_')[-1] if is_translation else None

        if isinstance(widget, forms.Textarea):
            classes = ['bo-textarea']
            if base_name in html_fields:
                classes.append('bo-textarea-html')
                attrs.setdefault('rows', 4)  # HTML-разметке нужно место
            elif base_name in compact_fields:
                classes.append('bo-textarea-compact')
                attrs['rows'] = 1  # принудительно — даже если уже выставлен
            else:
                attrs.setdefault('rows', 2)  # Описания компактные, пользователь может растянуть
            attrs['class'] = ' '.join(classes)
        elif isinstance(widget, (forms.NumberInput, forms.TextInput,
                                 forms.EmailInput, forms.URLInput)):
            attrs['class'] = 'bo-input'
        elif isinstance(widget, forms.ClearableFileInput):
            attrs['class'] = 'bo-file-input'
        # CheckboxInput (DELETE) и прочие — без класса.

        if is_translation and lang != 'ru' and 'placeholder' not in attrs:
            attrs['placeholder'] = '(пусто — берётся из ru)'


class LoginForm(forms.Form):
    username = forms.CharField(
        label=_('Логин'),
        max_length=150,
        widget=forms.TextInput(attrs={
            'autofocus': True,
            'autocomplete': 'username',
            'autocapitalize': 'off',
            'autocorrect': 'off',
            'spellcheck': 'false',
        }),
    )
    password = forms.CharField(
        label=_('Пароль'),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
    )

    error_messages = {
        'invalid_login': _('Неверный логин или пароль.'),
        'no_access': _('У этой учётной записи нет доступа в backoffice.'),
        'inactive': _('Учётная запись отключена.'),
    }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(self.error_messages['invalid_login'], code='invalid_login')
            if not self.user_cache.is_active:
                raise forms.ValidationError(self.error_messages['inactive'], code='inactive')
            if not self.user_cache.is_staff:
                raise forms.ValidationError(self.error_messages['no_access'], code='no_access')
        return self.cleaned_data

    def get_user(self):
        return self.user_cache


class LeadEditForm(forms.ModelForm):
    """Редактирование заявки в backoffice.

    Контактные поля (name/phone/city/origin/title) — read-only в шаблоне,
    форма ими не управляет. Менеджер меняет: статус, категория, заметка.
    """

    class Meta:
        model = Lead
        fields = ('status', 'category', 'manager_note')
        widgets = {
            'manager_note': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Что по звонку, договорённости, причина отказа.',
            }),
        }


# ===== Content: HomePage / ContactsPage edit forms ===========================
#
# Каждое translatable поле в форме разворачивается в три (`_ru`, `_kk`, `_en`).
# Шаблон рендерит их вручную с Alpine `x-show="lang === '..'"` — тогда у нас
# одна форма с правильным name'ом и POST с тремя значениями за раз.
#
# region не редактируется (singleton; menu-нав определяет регион). updated_at
# auto_now — не в форме.

HOME_TRANSLATABLE = (
    'hero_badge_text',
    'hero_title',
    'hero_subtitle',
    'hero_cta_primary_text',
    'hero_cta_primary_modal_title',
    'hero_cta_secondary_text',
    'hero_cta_secondary_modal_title',
    'about_label',
    'about_title',
    'about_body',
    'seo_title',
    'seo_description',
    'og_title',
    'og_description',
)


class HomePageEditForm(forms.ModelForm):
    """Редактирование HomePage с явными `_ru/_kk/_en` полями для каждого поля
    из translation.py."""

    HTML_FIELDS = frozenset({'hero_title'})

    # Поля, которые рендерятся ВНЕ тега <form id="home-edit-form"> (например SEO
    # после галереи). Им нужен HTML5-атрибут form="home-edit-form", иначе их
    # значения не уйдут с submit'ом.
    OUT_OF_FORM_BASES = frozenset({
        'seo_title', 'seo_description', 'og_title', 'og_description',
    })
    OUT_OF_FORM_FILE_FIELDS = frozenset({'og_image'})
    FORM_ID = 'home-edit-form'

    # Server-side лимиты на каждый файл-апроад (доп. защита поверх глобального
    # DATA_UPLOAD_MAX_MEMORY_SIZE в settings).
    IMAGE_MAX_BYTES = 5 * 1024 * 1024
    VIDEO_MAX_BYTES = 35 * 1024 * 1024

    class Meta:
        model = HomePage
        fields = ('hero_image', 'video_file', 'og_image') + _localized(*HOME_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self, html_fields=self.HTML_FIELDS)
        for name, field in self.fields.items():
            base = _strip_lang(name)
            if base in self.OUT_OF_FORM_BASES or name in self.OUT_OF_FORM_FILE_FIELDS:
                field.widget.attrs['form'] = self.FORM_ID

    def _check_max_size(self, file, limit, kind):
        """Soft size-проверка для одного файла. Если файл превышает лимит —
        бросаем ValidationError с понятной подсказкой (где сжать).

        `file` приходит как `UploadedFile` (есть атрибут .size). Если поле
        не менялось — это FieldFile с .size, обращаемся аккуратно."""
        if not file or not hasattr(file, 'size'):
            return file
        mb = file.size / 1024 / 1024
        limit_mb = limit // (1024 * 1024)
        if file.size > limit:
            raise forms.ValidationError(
                f'Файл {mb:.1f} MB больше лимита {limit_mb} MB для «{kind}». '
                'Сожми через CloudConvert / TinyPNG / HandBrake.'
            )
        return file

    def clean_hero_image(self):
        return self._check_max_size(self.cleaned_data.get('hero_image'),
                                    self.IMAGE_MAX_BYTES, 'hero')

    def clean_og_image(self):
        return self._check_max_size(self.cleaned_data.get('og_image'),
                                    self.IMAGE_MAX_BYTES, 'OG-картинка')

    def clean_video_file(self):
        return self._check_max_size(self.cleaned_data.get('video_file'),
                                    self.VIDEO_MAX_BYTES, 'шоурил')


CONTACTS_TRANSLATABLE = (
    'intro_title',
    'intro_text',
    'office_name',
    'office_address',
    'office_hours',
    'seo_title',
    'seo_description',
    'og_title',
    'og_description',
)


class ContactsPageEditForm(forms.ModelForm):
    """Редактирование ContactsPage с явными `_ru/_kk/_en` полями для каждого
    translatable поля из translation.py. Структурно повторяет HomePageEditForm."""

    # SEO/OG-блок рендерится после inline-formset (Departments). Поля, попадающие
    # вне основного <form id="contacts-edit-form">, получают HTML5-атрибут form=,
    # иначе их значения не уйдут с submit'ом. См. аналогичный паттерн в
    # HomePageEditForm.
    OUT_OF_FORM_BASES = frozenset({
        'seo_title', 'seo_description', 'og_title', 'og_description',
    })
    OUT_OF_FORM_FILE_FIELDS = frozenset({'og_image'})
    FORM_ID = 'contacts-edit-form'

    IMAGE_MAX_BYTES = 5 * 1024 * 1024

    class Meta:
        model = ContactsPage
        fields = (
            'latitude',
            'longitude',
            'map_zoom',
            'og_image',
        ) + _localized(*CONTACTS_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)
        for name, field in self.fields.items():
            base = _strip_lang(name)
            if base in self.OUT_OF_FORM_BASES or name in self.OUT_OF_FORM_FILE_FIELDS:
                field.widget.attrs['form'] = self.FORM_ID

    def _check_max_size(self, file, limit, kind):
        if not file or not hasattr(file, 'size'):
            return file
        mb = file.size / 1024 / 1024
        limit_mb = limit // (1024 * 1024)
        if file.size > limit:
            raise forms.ValidationError(
                f'Файл {mb:.1f} MB больше лимита {limit_mb} MB для «{kind}». '
                'Сожми через CloudConvert / TinyPNG.'
            )
        return file

    def clean_og_image(self):
        return self._check_max_size(self.cleaned_data.get('og_image'),
                                    self.IMAGE_MAX_BYTES, 'OG-картинка')


_CONTACTS_DEPARTMENT_TRANSLATABLE = ('title', 'description', 'hours')


class ContactsDepartmentItemForm(forms.ModelForm):
    class Meta:
        model = ContactsDepartment
        fields = (
            'order',
            'phone',
            'email',
        ) + _localized(*_CONTACTS_DEPARTMENT_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)


ContactsDepartmentFormSet = inlineformset_factory(
    parent_model=ContactsPage,
    model=ContactsDepartment,
    form=ContactsDepartmentItemForm,
    extra=1,
    can_delete=True,
)


# ===== Content: ProgramPage edit forms ======================================
#
# ProgramPage — самый большой лендинг (Hero + 7 секций с inline-моделями +
# секция «Внеклассные» без inline + SEO/OG). Все 7 inline сохраняются вместе
# с основной формой в одном POST'е (Contacts-pattern).

PROGRAM_TRANSLATABLE = (
    'hero_badge_text',
    'hero_title',
    'hero_subtitle',
    'hero_cta_primary_text',
    'hero_cta_secondary_text',
    'audience_label',
    'audience_title',
    'audience_subtitle',
    'benefits_label',
    'benefits_title',
    'benefits_subtitle',
    'programs_label',
    'programs_title',
    'programs_subtitle',
    'programs_cta_text',
    'team_label',
    'team_title',
    'team_subtitle',
    'certificate_label',
    'certificate_title',
    'certificate_subtitle',
    'certificate_cta_text',
    'activities_label',
    'activities_title',
    'activities_subtitle',
    'activities_cta_text',
    'stats_label',
    'stats_title',
    'stats_intro_text',
    'faq_label',
    'faq_title',
    'seo_title',
    'seo_description',
    'og_title',
    'og_description',
)


class ProgramPageEditForm(forms.ModelForm):
    """Редактирование ProgramPage. Структурно повторяет HomePageEditForm/
    ContactsPageEditForm — но самая большая (35 translatable полей × 3 языка =
    105 полей + 5 ImageField'ов + 4 числовых SEO).
    """

    HTML_FIELDS = frozenset({'hero_title'})

    # Поля-заголовки секций — в модели TextField (исторически), в UI это короткие
    # однострочные подписи. rows=1 чтобы не занимать пол-экрана пустым местом.
    COMPACT_FIELDS = frozenset({
        'audience_title', 'audience_subtitle',
        'benefits_title', 'benefits_subtitle',
        'programs_title', 'programs_subtitle',
        'team_title', 'team_subtitle',
        'certificate_title', 'certificate_subtitle',
        'activities_title', 'activities_subtitle',
        'stats_title',
        'faq_title',
        'hero_subtitle',
    })

    # SEO/OG-блок рендерится в шаблоне вне основного <form id="program-edit-form">
    # (после inline-formset'ов). Поля получают HTML5-атрибут form= чтобы их
    # значения уходили с submit'ом — паттерн HomePageEditForm/ContactsPageEditForm.
    OUT_OF_FORM_BASES = frozenset({
        'seo_title', 'seo_description', 'og_title', 'og_description',
    })
    OUT_OF_FORM_FILE_FIELDS = frozenset({'og_image'})
    FORM_ID = 'program-edit-form'

    IMAGE_MAX_BYTES = 5 * 1024 * 1024

    class Meta:
        model = ProgramPage
        fields = (
            'audience_photo_woman',
            'audience_photo_library',
            'benefits_photo_kid',
            'certificate_preview_image',
            'stats_photo',
            'og_image',
        ) + _localized(*PROGRAM_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(
            self,
            html_fields=self.HTML_FIELDS,
            compact_fields=self.COMPACT_FIELDS,
        )
        for name, field in self.fields.items():
            base = _strip_lang(name)
            if base in self.OUT_OF_FORM_BASES or name in self.OUT_OF_FORM_FILE_FIELDS:
                field.widget.attrs['form'] = self.FORM_ID

    def _check_max_size(self, file, limit, kind):
        if not file or not hasattr(file, 'size'):
            return file
        mb = file.size / 1024 / 1024
        limit_mb = limit // (1024 * 1024)
        if file.size > limit:
            raise forms.ValidationError(
                f'Файл {mb:.1f} MB больше лимита {limit_mb} MB для «{kind}». '
                'Сожми через CloudConvert / TinyPNG.'
            )
        return file

    def clean_audience_photo_woman(self):
        return self._check_max_size(self.cleaned_data.get('audience_photo_woman'),
                                    self.IMAGE_MAX_BYTES, 'фото девушки')

    def clean_audience_photo_library(self):
        return self._check_max_size(self.cleaned_data.get('audience_photo_library'),
                                    self.IMAGE_MAX_BYTES, 'фото библиотеки')

    def clean_benefits_photo_kid(self):
        return self._check_max_size(self.cleaned_data.get('benefits_photo_kid'),
                                    self.IMAGE_MAX_BYTES, 'фото ученика')

    def clean_certificate_preview_image(self):
        return self._check_max_size(self.cleaned_data.get('certificate_preview_image'),
                                    self.IMAGE_MAX_BYTES, 'образец сертификата')

    def clean_stats_photo(self):
        return self._check_max_size(self.cleaned_data.get('stats_photo'),
                                    self.IMAGE_MAX_BYTES, 'фото школы')

    def clean_og_image(self):
        return self._check_max_size(self.cleaned_data.get('og_image'),
                                    self.IMAGE_MAX_BYTES, 'OG-картинка')


# --- 7 inline-formset форм ---------------------------------------------------

_PROGRAM_AUDIENCE_TRANSLATABLE = ('title', 'description')
_PROGRAM_BENEFIT_TRANSLATABLE = ('title', 'description')
_PROGRAM_VARIANT_TRANSLATABLE = ('badge_text', 'title', 'tags', 'features', 'footer_label', 'footer_value')
_PROGRAM_TEAM_TRANSLATABLE = ('name', 'role', 'meta', 'quote')
_PROGRAM_CERT_FEATURE_TRANSLATABLE = ('title',)
_PROGRAM_STAT_TRANSLATABLE = ('value', 'label')
_PROGRAM_FAQ_TRANSLATABLE = ('question', 'answer')


def _relax_required(form, bases):
    """Сделать `required=False` для всех `_ru/_kk/_en` полей перечисленных bases.

    Используется в инлайн-формах с фиксированным числом слотов (audience / benefit /
    cert / stat): менеджер может оставить слот пустым (placeholder для будущего
    контента). Публичный шаблон скрывает пустые карточки через `{% if item.title %}`.
    """
    for base in bases:
        for lang in TRANSLATION_LANGS:
            name = f'{base}_{lang}'
            if name in form.fields:
                form.fields[name].required = False


def _limit_chars(form, bases, limit):
    """Ограничить длину `_ru/_kk/_en` полей перечисленных bases.

    Источник правды для лимита — UX: длина должна быть такой, чтобы перевод
    RU→KK/EN (обычно +30…50% символов) гарантированно помещался в карточку на
    публичной странице без переноса. Применяется к коротким заголовкам в
    inline-карточках audience/benefit/cert.
    """
    for base in bases:
        for lang in TRANSLATION_LANGS:
            name = f'{base}_{lang}'
            if name in form.fields:
                form.fields[name].max_length = limit
                form.fields[name].widget.attrs['maxlength'] = limit


class ProgramAudienceItemForm(forms.ModelForm):
    class Meta:
        model = ProgramAudienceItem
        fields = ('order', 'icon_svg') + _localized(*_PROGRAM_AUDIENCE_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)
        _relax_required(self, _PROGRAM_AUDIENCE_TRANSLATABLE)
        _limit_chars(self, ('title',), 60)


class ProgramBenefitItemForm(forms.ModelForm):
    class Meta:
        model = ProgramBenefitItem
        fields = ('order',) + _localized(*_PROGRAM_BENEFIT_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)
        _relax_required(self, _PROGRAM_BENEFIT_TRANSLATABLE)
        _limit_chars(self, ('title',), 60)


class ProgramVariantCardForm(forms.ModelForm):
    class Meta:
        model = ProgramVariantCard
        fields = ('order', 'badge_style') + _localized(*_PROGRAM_VARIANT_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)


class ProgramTeamMemberForm(forms.ModelForm):
    # name/role/meta — короткие подписи (имя, должность, мета-строка); в UI это
    # однострочники. quote — цитата, остаётся rows=2 по дефолту.
    COMPACT_FIELDS = frozenset({'name', 'role', 'meta'})

    class Meta:
        model = ProgramTeamMember
        fields = ('order', 'photo') + _localized(*_PROGRAM_TEAM_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self, compact_fields=self.COMPACT_FIELDS)


class ProgramCertificateFeatureForm(forms.ModelForm):
    class Meta:
        model = ProgramCertificateFeature
        fields = ('order', 'icon_svg') + _localized(*_PROGRAM_CERT_FEATURE_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)
        _relax_required(self, _PROGRAM_CERT_FEATURE_TRANSLATABLE)
        _limit_chars(self, ('title',), 60)


class ProgramStatForm(forms.ModelForm):
    class Meta:
        model = ProgramStat
        fields = ('order',) + _localized(*_PROGRAM_STAT_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)
        _relax_required(self, _PROGRAM_STAT_TRANSLATABLE)


class ProgramFaqItemForm(forms.ModelForm):
    class Meta:
        model = ProgramFaqItem
        fields = ('order',) + _localized(*_PROGRAM_FAQ_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)


def _program_formset(model, form, related_name, *, extra=1, can_delete=True, max_num=None):
    """Build inlineformset для inline-модели Программы.

    `extra=0, can_delete=False, max_num=4` — для секций с фиксированным числом
    слотов (audience / benefit / cert / stat). View предварительно гарантирует,
    что у программы ровно 4 строки для этих моделей (см. `_ensure_program_fixed_sections`).
    """
    kwargs = dict(
        parent_model=ProgramPage,
        model=model,
        form=form,
        extra=extra,
        can_delete=can_delete,
        fk_name='program_page',
    )
    if max_num is not None:
        kwargs['max_num'] = max_num
        kwargs['validate_max'] = True
    return inlineformset_factory(**kwargs)


# Фиксированные секции — ровно 4 слота. `extra=0` + `can_delete=False` + `max_num=4`.
# View использует `_ensure_program_fixed_sections` для гарантии 4 существующих строк.
ProgramAudienceFormSet = _program_formset(
    ProgramAudienceItem, ProgramAudienceItemForm, 'audience_items',
    extra=0, can_delete=False, max_num=4,
)
ProgramBenefitFormSet = _program_formset(
    ProgramBenefitItem, ProgramBenefitItemForm, 'benefit_items',
    extra=0, can_delete=False, max_num=4,
)
ProgramVariantFormSet = _program_formset(ProgramVariantCard, ProgramVariantCardForm, 'variant_cards')
ProgramTeamFormSet = _program_formset(ProgramTeamMember, ProgramTeamMemberForm, 'team_members', extra=0)
ProgramCertificateFeatureFormSet = _program_formset(
    ProgramCertificateFeature, ProgramCertificateFeatureForm, 'certificate_features',
    extra=0, can_delete=False, max_num=4,
)
ProgramStatFormSet = _program_formset(
    ProgramStat, ProgramStatForm, 'stats',
    extra=0, can_delete=False, max_num=4,
)
ProgramFaqFormSet = _program_formset(ProgramFaqItem, ProgramFaqItemForm, 'faq_items', extra=0)


# Имена related_name'ов, у которых должно быть ровно 4 строки. Используется в
# `_ensure_program_fixed_sections` (views.py) для гарантии 4 существующих
# строк перед инициализацией formset'а.
PROGRAM_FIXED_SLOT_SECTIONS = (
    ('audience_items', ProgramAudienceItem),
    ('benefit_items', ProgramBenefitItem),
    ('certificate_features', ProgramCertificateFeature),
    ('stats', ProgramStat),
)
PROGRAM_FIXED_SLOT_COUNT = 4


# Конфигурация inline-formset'ов для шаблона (порядок и связка name → prefix).
# Используется и views (создание/save), и template (отрисовка).
# Каждая запись: (prefix, formset_class, related_name на модели, человеко-читаемый label, list translatable bases).
PROGRAM_INLINE_FORMSETS = (
    ('audience_items', ProgramAudienceFormSet, 'audience_items',
     'Карточки «Кому подходит»', list(_PROGRAM_AUDIENCE_TRANSLATABLE)),
    ('benefit_items', ProgramBenefitFormSet, 'benefit_items',
     'Карточки «Что получает»', list(_PROGRAM_BENEFIT_TRANSLATABLE)),
    ('variant_cards', ProgramVariantFormSet, 'variant_cards',
     'Карточки программ', list(_PROGRAM_VARIANT_TRANSLATABLE)),
    ('team_members', ProgramTeamFormSet, 'team_members',
     'Члены команды', list(_PROGRAM_TEAM_TRANSLATABLE)),
    ('certificate_features', ProgramCertificateFeatureFormSet, 'certificate_features',
     'Карточки «Аттестат»', list(_PROGRAM_CERT_FEATURE_TRANSLATABLE)),
    ('stats', ProgramStatFormSet, 'stats',
     'Цифры', list(_PROGRAM_STAT_TRANSLATABLE)),
    ('faq_items', ProgramFaqFormSet, 'faq_items',
     'Вопросы FAQ', list(_PROGRAM_FAQ_TRANSLATABLE)),
)
