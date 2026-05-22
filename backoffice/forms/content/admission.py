"""AdmissionPage + AdmissionVariant edit-формы.

Структура (см. `memory/admission.md`):
  AdmissionPage    — singleton per region; общие тексты страницы.
  AdmissionVariant — (page × department × grade) per region.

Edit flow: отдельная страница per variant; на AdmissionPage edit — grid
с превью+ссылками на variant-страницы.
"""

from django import forms
from django.forms import inlineformset_factory

from admission.models import (
    AdmissionDocument,
    AdmissionIncludedItem,
    AdmissionPage,
    AdmissionPricingPlan,
    AdmissionTestingFeature,
    AdmissionVariant,
)

from .._common import (
    FileSizeMixin,
    _apply_backoffice_widget_classes,
    _limit_chars,
    _localized,
    _relax_required,
    apply_out_of_form_attrs,
)


# ----- AdmissionPage --------------------------------------------------------

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
    """Edit AdmissionPage — общие для региона тексты."""

    # `enrollment_fee_text` рендерится через |safe — поддерживает <span> разметку.
    HTML_FIELDS = frozenset({'enrollment_fee_text'})

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
ADMISSION_PAGE_INLINE_FORMSETS = (
    ('included_items', AdmissionIncludedItemFormSet, 'included_items',
     'Стоимость включает / Не включено', list(_ADMISSION_INCLUDED_TRANSLATABLE)),
    ('documents', AdmissionDocumentFormSet, 'documents',
     'Документы для зачисления', list(_ADMISSION_DOCUMENT_TRANSLATABLE)),
)


# ----- AdmissionVariant (per dept × grade) ----------------------------------

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


class AdmissionVariantEditForm(FileSizeMixin, forms.ModelForm):
    """Edit одного варианта (dept × grade). FK page/department/grade в форме
    НЕ редактируются — это контекст, фиксируется view'ом."""

    OUT_OF_FORM_BASES = frozenset({
        'seo_title', 'seo_description', 'og_title', 'og_description',
    })
    OUT_OF_FORM_FILE_FIELDS = frozenset()
    FORM_ID = 'admission-variant-edit-form'

    class Meta:
        model = AdmissionVariant
        fields = _localized(*ADMISSION_VARIANT_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)
        apply_out_of_form_attrs(
            self, self.FORM_ID, self.OUT_OF_FORM_BASES, self.OUT_OF_FORM_FILE_FIELDS,
        )


_ADMISSION_TESTING_FEATURE_TRANSLATABLE = ('title', 'description')
_ADMISSION_PRICING_PLAN_TRANSLATABLE = ('label', 'note')


class AdmissionTestingFeatureForm(forms.ModelForm):
    class Meta:
        model = AdmissionTestingFeature
        fields = ('order', 'icon_svg') + _localized(*_ADMISSION_TESTING_FEATURE_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)
        # Fixed-slot UX: все 4 карточки всегда в форме; менеджер может очистить
        # title (карточка скроется на сайте), но удалить — нельзя.
        _relax_required(self, _ADMISSION_TESTING_FEATURE_TRANSLATABLE)
        _limit_chars(self, ('title',), 60)


class AdmissionPricingPlanForm(forms.ModelForm):
    COMPACT_FIELDS = frozenset({'label', 'price_value', 'price_currency'})

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


# 4 фиксированных testing-features (2×2 grid).
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
