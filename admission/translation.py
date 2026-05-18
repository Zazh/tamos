from modeltranslation.translator import TranslationOptions, register

from .models import (
    AdmissionDocument,
    AdmissionIncludedItem,
    AdmissionPage,
    AdmissionPricingPlan,
    AdmissionTestingFeature,
    AdmissionVariant,
    Department,
    GradeGroup,
)


@register(Department)
class DepartmentTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(GradeGroup)
class GradeGroupTranslationOptions(TranslationOptions):
    fields = ('name', 'short_name')


@register(AdmissionPage)
class AdmissionPageTranslationOptions(TranslationOptions):
    fields = (
        'stage_consultation_title',
        'stage_consultation_meta',
        'stage_testing_title',
        'stage_testing_meta',
        'stage_result_title',
        'stage_result_meta',
        'stage_contract_title',
        'stage_contract_meta',
        'stage_enrollment_title',
        'stage_enrollment_meta',
        'testing_section_title',
        'result_section_title',
        'contract_section_title',
        'enrollment_section_title',
        'consultation_section_title',
        'breadcrumb_root_label',
        'department_dropdown_label',
        'grade_dropdown_label',
        'testing_rules_text',
        'testing_price_label',
        'testing_price_value',
        'enrollment_fee_text',
        'pricing_included_title',
        'pricing_excluded_title',
        'enrollment_lead',
        'documents_title',
        'consultation_lead',
        'consultation_cta_text',
    )


@register(AdmissionIncludedItem)
class AdmissionIncludedItemTranslationOptions(TranslationOptions):
    fields = ('text',)


@register(AdmissionDocument)
class AdmissionDocumentTranslationOptions(TranslationOptions):
    fields = ('text',)


@register(AdmissionVariant)
class AdmissionVariantTranslationOptions(TranslationOptions):
    fields = (
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


@register(AdmissionTestingFeature)
class AdmissionTestingFeatureTranslationOptions(TranslationOptions):
    fields = ('title', 'description')


@register(AdmissionPricingPlan)
class AdmissionPricingPlanTranslationOptions(TranslationOptions):
    fields = ('badge_text', 'label', 'note')
