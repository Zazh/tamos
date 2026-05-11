from modeltranslation.translator import TranslationOptions, register

from .models import (
    ProgramActivityItem,
    ProgramAudienceItem,
    ProgramBenefitItem,
    ProgramCertificateFeature,
    ProgramFaqItem,
    ProgramPage,
    ProgramStat,
    ProgramTeamMember,
    ProgramVariantCard,
)


@register(ProgramPage)
class ProgramPageTranslationOptions(TranslationOptions):
    fields = (
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
    )


@register(ProgramAudienceItem)
class ProgramAudienceItemTranslationOptions(TranslationOptions):
    fields = ('title', 'description')


@register(ProgramBenefitItem)
class ProgramBenefitItemTranslationOptions(TranslationOptions):
    fields = ('title', 'description')


@register(ProgramVariantCard)
class ProgramVariantCardTranslationOptions(TranslationOptions):
    fields = ('badge_text', 'title', 'tags', 'features', 'footer_label', 'footer_value')


@register(ProgramTeamMember)
class ProgramTeamMemberTranslationOptions(TranslationOptions):
    fields = ('name', 'role', 'meta', 'quote')


@register(ProgramCertificateFeature)
class ProgramCertificateFeatureTranslationOptions(TranslationOptions):
    fields = ('title',)


@register(ProgramActivityItem)
class ProgramActivityItemTranslationOptions(TranslationOptions):
    fields = ('time_label', 'title', 'category', 'description')


@register(ProgramStat)
class ProgramStatTranslationOptions(TranslationOptions):
    fields = ('value', 'label')


@register(ProgramFaqItem)
class ProgramFaqItemTranslationOptions(TranslationOptions):
    fields = ('question', 'answer')
