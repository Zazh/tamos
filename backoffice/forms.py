from django import forms
from django.conf import settings
from django.contrib.auth import authenticate
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _

from activities.models import (
    Activity,
    ActivityGroup,
    ActivitySection,
    ScheduleSlot,
)
from admission.models import (
    AdmissionDocument,
    AdmissionIncludedItem,
    AdmissionPage,
    AdmissionPricingPlan,
    AdmissionTestingFeature,
    AdmissionVariant,
)
from blog.models import BlogCategory, BlogPost, BlogTag
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


# ===== Content: AdmissionPage + AdmissionVariant edit forms =================
#
# Структура (см. memory/admission.md):
#   AdmissionPage     — singleton per region; общие тексты страницы (stepper,
#                       UI-лейблы, секции, правила тестирования, документы и т.д.)
#   AdmissionVariant  — (page × department × grade) — варианты страницы. На каждый
#                       регион 6 вариантов: 3 RU (1, 2-7, 8-11) + 3 KZ (1, 2-6, 7-11).
#                       Hero, lead'ы этапов, prising и SEO/OG — здесь.
#
# Edit flow (см. ответ юзера): отдельная страница per variant, на AdmissionPage
# edit'е — grid с превью+ссылками на каждую из 6 variant-страниц.

ADMISSION_PAGE_TRANSLATABLE = (
    # Stepper (5 этапов × 2: title + meta) — короткие подписи
    'stage_consultation_title', 'stage_consultation_meta',
    'stage_testing_title', 'stage_testing_meta',
    'stage_result_title', 'stage_result_meta',
    'stage_contract_title', 'stage_contract_meta',
    'stage_enrollment_title', 'stage_enrollment_meta',
    # Заголовки h3 секций
    'testing_section_title',
    'result_section_title',
    'contract_section_title',
    'enrollment_section_title',
    'consultation_section_title',
    # UI-лейблы
    'breadcrumb_root_label',
    'department_dropdown_label',
    'grade_dropdown_label',
    # Этап «Тестирование» — общая часть
    'testing_rules_text',
    'testing_price_label',
    'testing_price_value',
    # Этап «Договор» — общая часть
    'enrollment_fee_text',
    'pricing_included_title',
    'pricing_excluded_title',
    # Этап «Зачисление»
    'enrollment_lead',
    'documents_title',
    # Этап «Консультация»
    'consultation_lead',
    'consultation_cta_text',
)


class AdmissionPageEditForm(forms.ModelForm):
    """Редактирование AdmissionPage — общие для региона тексты."""

    # HTML-textarea: `enrollment_fee_text` рендерится через |safe (поддерживает
    # <span class="font-bold text-black">…</span>). Для разметки нужно больше места.
    HTML_FIELDS = frozenset({'enrollment_fee_text'})

    # Short-title поля — однострочники (TextField исторически, в UI это короткие
    # подписи; rows=1 чтобы не съедать пол-экрана).
    COMPACT_FIELDS = frozenset({
        'stage_consultation_title', 'stage_consultation_meta',
        'stage_testing_title', 'stage_testing_meta',
        'stage_result_title', 'stage_result_meta',
        'stage_contract_title', 'stage_contract_meta',
        'stage_enrollment_title', 'stage_enrollment_meta',
        'testing_section_title',
        'result_section_title',
        'contract_section_title',
        'enrollment_section_title',
        'consultation_section_title',
        'breadcrumb_root_label',
        'department_dropdown_label',
        'grade_dropdown_label',
        'testing_price_label',
        'testing_price_value',
        'pricing_included_title',
        'pricing_excluded_title',
        'documents_title',
        'consultation_cta_text',
    })

    FORM_ID = 'admission-page-edit-form'

    class Meta:
        model = AdmissionPage
        fields = _localized(*ADMISSION_PAGE_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(
            self,
            html_fields=self.HTML_FIELDS,
            compact_fields=self.COMPACT_FIELDS,
        )


_ADMISSION_INCLUDED_TRANSLATABLE = ('text',)
_ADMISSION_DOCUMENT_TRANSLATABLE = ('text',)


class AdmissionIncludedItemForm(forms.ModelForm):
    class Meta:
        model = AdmissionIncludedItem
        fields = ('order', 'is_excluded') + _localized(*_ADMISSION_INCLUDED_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)


class AdmissionDocumentForm(forms.ModelForm):
    class Meta:
        model = AdmissionDocument
        fields = ('order',) + _localized(*_ADMISSION_DOCUMENT_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)


AdmissionIncludedItemFormSet = inlineformset_factory(
    parent_model=AdmissionPage,
    model=AdmissionIncludedItem,
    form=AdmissionIncludedItemForm,
    extra=0,
    can_delete=True,
    fk_name='page',
)

AdmissionDocumentFormSet = inlineformset_factory(
    parent_model=AdmissionPage,
    model=AdmissionDocument,
    form=AdmissionDocumentForm,
    extra=0,
    can_delete=True,
    fk_name='page',
)


# Конфигурация формсетов AdmissionPage — единое место правды для view/template.
# Каждая запись: (prefix, FormSet, related_name, label, translatable_bases).
ADMISSION_PAGE_INLINE_FORMSETS = (
    ('included_items', AdmissionIncludedItemFormSet, 'included_items',
     'Стоимость включает / Не включено', list(_ADMISSION_INCLUDED_TRANSLATABLE)),
    ('documents', AdmissionDocumentFormSet, 'documents',
     'Документы для зачисления', list(_ADMISSION_DOCUMENT_TRANSLATABLE)),
)


# --- AdmissionVariant (per dept × grade) ----------------------------------

ADMISSION_VARIANT_TRANSLATABLE = (
    'h1',
    'hero_lead',
    'testing_lead',
    'result_intro',
    'result_detail',
    'pricing_lead',
    'seo_title',
    'seo_description',
    'og_title',
    'og_description',
)


class AdmissionVariantEditForm(forms.ModelForm):
    """Редактирование одного варианта (dept × grade). FK page/department/grade
    в форме НЕ редактируются — это контекст, фиксируется view'ом."""

    OUT_OF_FORM_BASES = frozenset({
        'seo_title', 'seo_description', 'og_title', 'og_description',
    })
    OUT_OF_FORM_FILE_FIELDS = frozenset({'og_image'})
    FORM_ID = 'admission-variant-edit-form'

    IMAGE_MAX_BYTES = 5 * 1024 * 1024

    class Meta:
        model = AdmissionVariant
        fields = ('og_image',) + _localized(*ADMISSION_VARIANT_TRANSLATABLE)

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
        return self._check_max_size(
            self.cleaned_data.get('og_image'), self.IMAGE_MAX_BYTES, 'OG-картинка'
        )


_ADMISSION_TESTING_FEATURE_TRANSLATABLE = ('title', 'description')
_ADMISSION_PRICING_PLAN_TRANSLATABLE = ('badge_text', 'label', 'note')


class AdmissionTestingFeatureForm(forms.ModelForm):
    class Meta:
        model = AdmissionTestingFeature
        fields = ('order', 'icon_svg') + _localized(*_ADMISSION_TESTING_FEATURE_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)
        # Fixed-slot UX: все 4 карточки всегда есть в форме; менеджер может
        # очистить заголовок (карточка скроется на сайте), но удалить — нельзя.
        _relax_required(self, _ADMISSION_TESTING_FEATURE_TRANSLATABLE)
        _limit_chars(self, ('title',), 60)


class AdmissionPricingPlanForm(forms.ModelForm):
    # `label/note/price_value/price_currency` — короткие подписи, в UI однострочники.
    COMPACT_FIELDS = frozenset({'label', 'price_value', 'price_currency', 'badge_text'})

    class Meta:
        model = AdmissionPricingPlan
        fields = (
            'order',
            'highlight',
            'price_value',
            'price_currency',
            'icon_svg',
        ) + _localized(*_ADMISSION_PRICING_PLAN_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self, compact_fields=self.COMPACT_FIELDS)


def _admission_variant_formset(model, form, *, extra=1, can_delete=True, max_num=None):
    kwargs = dict(
        parent_model=AdmissionVariant,
        model=model,
        form=form,
        extra=extra,
        can_delete=can_delete,
        fk_name='variant',
    )
    if max_num is not None:
        kwargs['max_num'] = max_num
        kwargs['validate_max'] = True
    return inlineformset_factory(**kwargs)


# 4 фиксированных testing-features (по дизайну: 2×2 grid). Менеджер может
# оставить title пустым — карточка скроется на публичной странице (см. view).
AdmissionTestingFeatureFormSet = _admission_variant_formset(
    AdmissionTestingFeature, AdmissionTestingFeatureForm,
    extra=0, can_delete=False, max_num=4,
)

# Pricing-plans — гибкое количество (3 в seed grade-1; для остальных variant'ов
# может быть 1 = «Полная оплата»). Collapsible accordion в UI.
AdmissionPricingPlanFormSet = _admission_variant_formset(
    AdmissionPricingPlan, AdmissionPricingPlanForm,
    extra=0, can_delete=True,
)


# related_name+model для гарантии 4 testing-features на variant (view-хелпер
# `_ensure_admission_fixed_sections`, аналог `_ensure_program_fixed_sections`).
ADMISSION_VARIANT_FIXED_SLOT_SECTIONS = (
    ('testing_features', AdmissionTestingFeature),
)
ADMISSION_VARIANT_FIXED_SLOT_COUNT = 4


ADMISSION_VARIANT_INLINE_FORMSETS = (
    ('testing_features', AdmissionTestingFeatureFormSet, 'testing_features',
     'Карточки этапа «Тестирование» (ровно 4)',
     list(_ADMISSION_TESTING_FEATURE_TRANSLATABLE)),
    ('pricing_plans', AdmissionPricingPlanFormSet, 'pricing_plans',
     'Прайс-карты этапа «Договор и взнос»',
     list(_ADMISSION_PRICING_PLAN_TRANSLATABLE)),
)


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


# ===== Content: Activities (Activity / ActivityGroup / ScheduleSlot) =======
#
# Структура (после редизайна 2026-05-18):
#   Region → ActivitySection (global) → Activity → ActivityGroup → ScheduleSlot
#
# UX:
#   /backoffice/content/activities/                       — list регионов
#   /backoffice/content/activities/region/<r>/            — каталог: list collapsible
#                                                          аккордеонов с inline-формой
#                                                          (Activity целиком).
#   /backoffice/content/activities/<activity>/save/       — POST save Activity (из аккордеона)
#   /backoffice/content/activities/group/<g>/             — edit Group + ScheduleSlot inline
#
# Тренер теперь — просто строки на Activity (teacher_name / teacher_phone / teacher_bio).
# Отдельной модели Teacher больше НЕТ.

ACTIVITY_TRANSLATABLE = ('name', 'description', 'location')
ACTIVITY_GROUP_TRANSLATABLE = ('label', 'teacher_name', 'teacher_bio')


class ActivityEditForm(forms.ModelForm):
    """Edit одного кружка. region read-only из view, section — dropdown
    (3 глобальные секции). Тренер задаётся на УРОВНЕ ГРУППЫ (`ActivityGroup.teacher_*`),
    не здесь.
    """

    FORM_ID_TPL = 'activity-{pk}-form'  # уникальный id на каждый аккордеон в catalog
    COMPACT_FIELDS = frozenset({'name', 'location'})

    class Meta:
        model = Activity
        fields = (
            'section',
            'is_published',
            'is_featured',
            'order',
        ) + _localized(*ACTIVITY_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self, compact_fields=self.COMPACT_FIELDS)
        self.fields['section'].widget.attrs['class'] = 'bo-select'
        # Order — hidden (DnD сортировка в catalog).
        self.fields['order'].widget = forms.HiddenInput()
        # name — maxlength=60 на input уровне (модель тоже max_length=60).
        for lang in TRANSLATION_LANGS:
            name_field = f'name_{lang}'
            if name_field in self.fields:
                self.fields[name_field].widget.attrs['maxlength'] = 60


class ActivityGroupForm(forms.ModelForm):
    """Edit одной группы внутри activity. classes — multi-checkbox 1..11.

    Тренер (имя/телефон/био) — на уровне группы, потому что у разных групп
    одного кружка могут быть разные тренера.
    """

    classes = forms.MultipleChoiceField(
        choices=[(i, str(i)) for i in range(1, 12)],
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Классы',
        help_text='Если ни один класс не выбран — группа считается «все 1–11».',
    )

    COMPACT_FIELDS = frozenset({'teacher_name'})

    class Meta:
        model = ActivityGroup
        fields = (
            'order',
            'teacher_phone',
            'price',
            'students_status',
            'min_students',
            'max_students',
            'classes',
        ) + _localized(*ACTIVITY_GROUP_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.initial['classes'] = [str(c) for c in (self.instance.classes or [])]
        _apply_backoffice_widget_classes(self, compact_fields=self.COMPACT_FIELDS)
        self.fields['students_status'].widget.attrs['class'] = 'bo-select'
        # Order — hidden (используется только для сортировки между группами;
        # значение выставляется при создании в `content_activities_group_add`).
        self.fields['order'].widget = forms.HiddenInput()

    def clean_classes(self):
        raw = self.cleaned_data.get('classes') or []
        try:
            values = sorted({int(c) for c in raw if 1 <= int(c) <= 11})
        except (TypeError, ValueError) as exc:
            raise forms.ValidationError('Класс должен быть числом от 1 до 11.') from exc
        return values or list(range(1, 12))

    def clean(self):
        cleaned = super().clean()
        min_s = cleaned.get('min_students')
        max_s = cleaned.get('max_students')
        if min_s is not None and max_s is not None and min_s > max_s:
            raise forms.ValidationError('Минимум учеников не может быть больше максимума.')
        return cleaned


class ScheduleSlotForm(forms.ModelForm):
    """Edit одного слота расписания группы."""

    class Meta:
        model = ScheduleSlot
        fields = ('order', 'day', 'start_time', 'end_time')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)
        self.fields['day'].widget.attrs['class'] = 'bo-select'
        for f in ('start_time', 'end_time'):
            self.fields[f].widget.input_type = 'time'
            self.fields[f].widget.attrs['class'] = 'bo-input'


ActivityGroupFormSet = inlineformset_factory(
    parent_model=Activity,
    model=ActivityGroup,
    form=ActivityGroupForm,
    extra=0,
    can_delete=True,
    fk_name='activity',
)

ScheduleSlotFormSet = inlineformset_factory(
    parent_model=ActivityGroup,
    model=ScheduleSlot,
    form=ScheduleSlotForm,
    extra=0,
    can_delete=True,
    fk_name='group',
)


# ===== Content: Blog (раздел «Лента») =======================================
#
# Базовая идея: один пост = одна edit-форма. Все переводимые поля
# (title/lead/cover_caption/cover_alt/content) развёрнуты в `_ru/_kk/_en`.
# Теги передаются отдельным hidden-полем `tags_json` со списком
# `[{slug, name}]` — view парсит, резолвит существующие BlogTag по
# (region, slug), отсутствующие создаёт; затем синхронизирует M2M.
# Категории и теги создаются на отдельной странице taxonomy.

BLOG_POST_TRANSLATABLE = (
    'title',
    'lead',
    'cover_caption',
    'cover_alt',
    'content',
    'seo_title',
    'seo_description',
    'og_title',
    'og_description',
)

# SEO/OG поля рендерятся в отдельной панели ВНЕ основного <form> (как у
# Home/Contacts/Program/Admission). Связь — через HTML5 `form="blog-edit-form"`
# атрибут. Шаблон знает этот список и кладёт нужные включает в правильное место.
BLOG_POST_OUT_OF_FORM_BASES = (
    'seo_title',
    'seo_description',
    'og_title',
    'og_description',
)


class BlogPostEditForm(forms.ModelForm):
    """Редактирование одного `BlogPost`. Регион/категория — обязательные,
    но регион нельзя поменять (singleton-per-region scoping).

    Поле `tags_json` — hidden input, заполняется Alpine-компонентом
    `boTagPicker`. Формат: JSON-массив `[{"slug": "...", "name": "..."}]`.
    """

    HTML_FIELDS = frozenset({'content'})
    COMPACT_FIELDS = frozenset({
        'seo_title', 'og_title',
        'cover_caption', 'cover_alt',
    })
    OUT_OF_FORM_BASES = frozenset({
        'seo_title', 'seo_description', 'og_title', 'og_description',
    })
    # Поля рендерятся ВНЕ <form id="blog-edit-form"> (Теги/Публикация/SEO-картинка),
    # но должны сабмититься вместе с формой → HTML5 form= атрибут.
    OUT_OF_FORM_FILE_FIELDS = frozenset({
        'og_image', 'is_published', 'published_at', 'tags_json',
    })
    FORM_ID = 'blog-edit-form'

    IMAGE_MAX_BYTES = 5 * 1024 * 1024

    tags_json = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        initial='[]',
    )

    class Meta:
        model = BlogPost
        fields = (
            'region',
            'category',
            'slug',
            'cover_image',
            'og_image',
            'is_published',
            'published_at',
        ) + _localized(*BLOG_POST_TRANSLATABLE)
        widgets = {
            'published_at': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'bo-input',
            }),
            'is_published': forms.CheckboxInput(),
        }

    def __init__(self, *args, user=None, region=None, **kwargs):
        """`user`/`region` оставлены для совместимости с create-view;
        категории/теги теперь глобальные, region-фильтр не применяется."""
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(
            self,
            html_fields=self.HTML_FIELDS,
            compact_fields=self.COMPACT_FIELDS,
        )

        # Slug пользователю не показываем — auto-gen из title + 4-hex
        # суффикс на создании (см. views._auto_slug). На edit нужен для
        # form-valid, рендерится как hidden.
        self.fields['slug'].widget = forms.HiddenInput()
        self.fields['slug'].required = False

        # Поля, рендерящиеся ВНЕ <form id="blog-edit-form"> (панель SEO/OG после
        # основной формы) — HTML5 form= связывает их обратно. Без этого их
        # значения не уходят с submit'ом.
        for name, field in self.fields.items():
            base = _strip_lang(name)
            if base in self.OUT_OF_FORM_BASES or name in self.OUT_OF_FORM_FILE_FIELDS:
                field.widget.attrs['form'] = self.FORM_ID

        # Категории — глобальные, без фильтра по региону.
        self.fields['category'].queryset = BlogCategory.objects.all().order_by('order', 'name')
        self.fields['category'].widget.attrs['class'] = 'bo-select'

        # Регион:
        # - на edit (instance.pk есть) — hidden, регион поста не меняется;
        # - на create — обычный select, ограниченный регионом менеджера (или всеми для su).
        instance = kwargs.get('instance')
        if instance and instance.pk:
            self.fields['region'].widget = forms.HiddenInput()
            self.fields['region'].required = False
        else:
            from regions.models import Region
            if user is not None and user.is_superuser:
                self.fields['region'].queryset = Region.objects.filter(is_active=True)
            elif user is not None and getattr(user, 'manager_region_id', None):
                self.fields['region'].queryset = Region.objects.filter(pk=user.manager_region_id)
                self.fields['region'].initial = user.manager_region_id
            else:
                self.fields['region'].queryset = Region.objects.none()
            self.fields['region'].widget.attrs['class'] = 'bo-select'

        # `datetime-local` ждёт ISO-формат без таймзоны. Django по умолчанию
        # рендерит локализованную строку — переопределяем.
        if self.instance and self.instance.pk and self.instance.published_at:
            self.initial['published_at'] = self.instance.published_at.strftime('%Y-%m-%dT%H:%M')

        # Pre-fill tags_json из текущей M2M (для GET). names на 3 языках —
        # tag-picker реактивно меняет отображение при смене таба RU/KK/EN.
        if self.instance and self.instance.pk:
            tags = [
                {
                    'slug': t.slug,
                    'name': t.name,
                    'names': {
                        'ru': t.name_ru or t.name or '',
                        'kk': t.name_kk or '',
                        'en': t.name_en or '',
                    },
                }
                for t in self.instance.tags.all().order_by('order', 'name')
            ]
            import json as _json
            self.initial['tags_json'] = _json.dumps(tags, ensure_ascii=False)

    def _check_image_size(self, file, label):
        if not file or not hasattr(file, 'size'):
            return file
        if file.size > self.IMAGE_MAX_BYTES:
            mb = file.size / 1024 / 1024
            limit_mb = self.IMAGE_MAX_BYTES // (1024 * 1024)
            raise forms.ValidationError(
                f'{label}: файл {mb:.1f} MB больше лимита {limit_mb} MB. '
                'Сожми через CloudConvert / TinyPNG.'
            )
        return file

    def clean_cover_image(self):
        return self._check_image_size(self.cleaned_data.get('cover_image'), 'Обложка')

    def clean_og_image(self):
        return self._check_image_size(self.cleaned_data.get('og_image'), 'OG-картинка')

    def clean_tags_json(self):
        """Валидирует JSON, возвращает уже распарсенный список dict'ов
        `[{slug, name, names?}]` — view использует их для sync M2M.
        Поле `names` (dict ru/kk/en) опционально — нужно только при создании
        нового тега, чтобы заполнить переводы сразу."""
        import json as _json
        raw = self.cleaned_data.get('tags_json') or '[]'
        try:
            parsed = _json.loads(raw)
        except ValueError:
            raise forms.ValidationError('Невалидный JSON списка тегов.')
        if not isinstance(parsed, list):
            raise forms.ValidationError('Список тегов должен быть массивом.')

        cleaned: list[dict] = []
        seen: set[str] = set()
        for item in parsed[:30]:  # hard cap на сторону клиента
            if not isinstance(item, dict):
                continue
            slug = str(item.get('slug', '')).strip().lower()
            name = str(item.get('name', '')).strip()
            if not slug or not name or slug in seen:
                continue
            safe_slug = ''.join(c for c in slug if c.isalnum() or c == '-')[:64].strip('-')
            if not safe_slug:
                continue
            seen.add(safe_slug)
            entry = {'slug': safe_slug, 'name': name[:80]}
            # opt-in names на 3 языках (если picker передал)
            raw_names = item.get('names') if isinstance(item.get('names'), dict) else None
            if raw_names:
                entry['names'] = {
                    lang: str(raw_names.get(lang, ''))[:80]
                    for lang in ('ru', 'kk', 'en')
                }
            cleaned.append(entry)
        return cleaned


class BlogCategoryItemForm(forms.ModelForm):
    """Inline-форма для редактирования одной BlogCategory на странице taxonomy.
    Order пользователю не показываем — порядок назначается автоматически."""

    class Meta:
        model = BlogCategory
        fields = _localized('name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)


class BlogTagItemForm(forms.ModelForm):
    """Inline-форма для редактирования одного BlogTag на странице taxonomy."""

    class Meta:
        model = BlogTag
        fields = _localized('name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)


class BlogCategoryCreateForm(forms.Form):
    """Быстрое создание новой BlogCategory из taxonomy-страницы.
    Теперь глобальная (без region). Slug auto из name."""

    name_ru = forms.CharField(max_length=80, widget=forms.TextInput(attrs={'class': 'bo-input'}))

    def __init__(self, *args, user=None, **kwargs):
        # `user` оставлен для совместимости с view; не используется.
        super().__init__(*args, **kwargs)


class BlogTagCreateForm(BlogCategoryCreateForm):
    """То же что BlogCategoryCreateForm — одинаковая структура полей."""
    pass
