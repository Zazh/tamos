"""ProgramPage edit-форма + 6 inline-formset'ов.

Самый большой лендинг (Hero + 7 секций; 35 translatable полей × 3 языка =
105 полей + 5 ImageField'ов). Все inline сохраняются вместе с основной
формой в одном POST'е (Contacts-pattern).

`PROGRAM_INLINE_FORMSETS` — единое место правды для view и template:
порядок секций + prefix + label + translatable bases.
"""

from django import forms
from django.forms import inlineformset_factory

from programs.models import (
    ProgramAudienceItem,
    ProgramBenefitItem,
    ProgramCertificateFeature,
    ProgramFaqItem,
    ProgramPage,
    ProgramStat,
    ProgramVariantCard,
)

from .._common import (
    FileSizeMixin,
    TRANSLATION_LANGS,
    _apply_backoffice_widget_classes,
    _limit_chars,
    _localized,
    _relax_required,
    apply_out_of_form_attrs,
)


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


class ProgramPageEditForm(FileSizeMixin, forms.ModelForm):
    HTML_FIELDS = frozenset({'hero_title'})

    # Заголовки секций — в модели TextField (исторически), в UI это короткие
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
        apply_out_of_form_attrs(
            self, self.FORM_ID, self.OUT_OF_FORM_BASES, self.OUT_OF_FORM_FILE_FIELDS,
        )

    def clean_audience_photo_woman(self):
        return self._check_size(self.cleaned_data.get('audience_photo_woman'),
                                self.IMAGE_MAX_BYTES, 'фото девушки')

    def clean_audience_photo_library(self):
        return self._check_size(self.cleaned_data.get('audience_photo_library'),
                                self.IMAGE_MAX_BYTES, 'фото библиотеки')

    def clean_benefits_photo_kid(self):
        return self._check_size(self.cleaned_data.get('benefits_photo_kid'),
                                self.IMAGE_MAX_BYTES, 'фото ученика')

    def clean_certificate_preview_image(self):
        return self._check_size(self.cleaned_data.get('certificate_preview_image'),
                                self.IMAGE_MAX_BYTES, 'образец сертификата')

    def clean_stats_photo(self):
        return self._check_size(self.cleaned_data.get('stats_photo'),
                                self.IMAGE_MAX_BYTES, 'фото школы')

    def clean_og_image(self):
        return self._check_size(self.cleaned_data.get('og_image'),
                                self.IMAGE_MAX_BYTES, 'OG-картинка')


# --- 6 inline-formset форм ---------------------------------------------------

_PROGRAM_AUDIENCE_TRANSLATABLE = ('title', 'description')
_PROGRAM_BENEFIT_TRANSLATABLE = ('title', 'description')
_PROGRAM_VARIANT_TRANSLATABLE = ('badge_text', 'title', 'tags', 'features', 'footer_label', 'footer_value')
_PROGRAM_CERT_FEATURE_TRANSLATABLE = ('title',)
_PROGRAM_STAT_TRANSLATABLE = ('value', 'label')
_PROGRAM_FAQ_TRANSLATABLE = ('question', 'answer')


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
        for lang in TRANSLATION_LANGS:
            name = f'label_{lang}'
            if name in self.fields:
                self.fields[name].widget = forms.Textarea()
        _apply_backoffice_widget_classes(self)
        _relax_required(self, _PROGRAM_STAT_TRANSLATABLE)


class ProgramFaqItemForm(forms.ModelForm):
    class Meta:
        model = ProgramFaqItem
        fields = ('order',) + _localized(*_PROGRAM_FAQ_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)


def _program_formset(model, form, *, extra=1, can_delete=True, max_num=None):
    """Build inlineformset для inline-модели Программы. `extra=0, can_delete=False,
    max_num=4` — для секций с фиксированным числом слотов; view предварительно
    гарантирует 4 строки (см. `_ensure_program_fixed_sections`)."""
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


# Фиксированные секции — ровно 4 слота.
ProgramAudienceFormSet = _program_formset(
    ProgramAudienceItem, ProgramAudienceItemForm,
    extra=0, can_delete=False, max_num=4,
)
ProgramBenefitFormSet = _program_formset(
    ProgramBenefitItem, ProgramBenefitItemForm,
    extra=0, can_delete=False, max_num=4,
)
ProgramVariantFormSet = _program_formset(ProgramVariantCard, ProgramVariantCardForm)
ProgramCertificateFeatureFormSet = _program_formset(
    ProgramCertificateFeature, ProgramCertificateFeatureForm,
    extra=0, can_delete=False, max_num=4,
)
ProgramStatFormSet = _program_formset(
    ProgramStat, ProgramStatForm,
    extra=0, can_delete=False, max_num=4,
)
ProgramFaqFormSet = _program_formset(ProgramFaqItem, ProgramFaqItemForm, extra=0)


# related_name+model для гарантии 4 строк (view-хелпер `_ensure_program_fixed_sections`).
PROGRAM_FIXED_SLOT_SECTIONS = (
    ('audience_items', ProgramAudienceItem),
    ('benefit_items', ProgramBenefitItem),
    ('certificate_features', ProgramCertificateFeature),
    ('stats', ProgramStat),
)
PROGRAM_FIXED_SLOT_COUNT = 4


# Конфигурация inline-formset'ов: единое место правды для views и templates.
# Каждая запись: (prefix, formset_class, related_name, label, translatable_bases).
PROGRAM_INLINE_FORMSETS = (
    ('audience_items', ProgramAudienceFormSet, 'audience_items',
     'Карточки «Кому подходит»', list(_PROGRAM_AUDIENCE_TRANSLATABLE)),
    ('benefit_items', ProgramBenefitFormSet, 'benefit_items',
     'Карточки «Что получает»', list(_PROGRAM_BENEFIT_TRANSLATABLE)),
    ('variant_cards', ProgramVariantFormSet, 'variant_cards',
     'Карточки программ', list(_PROGRAM_VARIANT_TRANSLATABLE)),
    ('certificate_features', ProgramCertificateFeatureFormSet, 'certificate_features',
     'Карточки «Аттестат»', list(_PROGRAM_CERT_FEATURE_TRANSLATABLE)),
    ('stats', ProgramStatFormSet, 'stats',
     'Цифры', list(_PROGRAM_STAT_TRANSLATABLE)),
    ('faq_items', ProgramFaqFormSet, 'faq_items',
     'Вопросы FAQ', list(_PROGRAM_FAQ_TRANSLATABLE)),
)
