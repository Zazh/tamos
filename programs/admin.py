from django.contrib import admin
from modeltranslation.admin import TabbedTranslationAdmin, TranslationStackedInline

from regions.admin import RegionScopedAdminMixin

from .models import (
    ProgramAudienceItem,
    ProgramBenefitItem,
    ProgramCertificateFeature,
    ProgramFaqItem,
    ProgramPage,
    ProgramStat,
    ProgramTeamMember,
    ProgramVariantCard,
)


class ProgramAudienceItemInline(TranslationStackedInline):
    model = ProgramAudienceItem
    extra = 0
    fields = ('order', 'title', 'description', 'icon_svg')


class ProgramBenefitItemInline(TranslationStackedInline):
    model = ProgramBenefitItem
    extra = 0
    fields = ('order', 'title', 'description')


class ProgramVariantCardInline(TranslationStackedInline):
    model = ProgramVariantCard
    extra = 0
    fields = (
        'order', 'badge_text', 'badge_style', 'title',
        'tags', 'features', 'footer_label', 'footer_value',
    )


class ProgramTeamMemberInline(TranslationStackedInline):
    model = ProgramTeamMember
    extra = 0
    fields = ('order', 'photo', 'name', 'role', 'meta', 'quote')


class ProgramCertificateFeatureInline(TranslationStackedInline):
    model = ProgramCertificateFeature
    extra = 0
    fields = ('order', 'title', 'icon_svg')


class ProgramStatInline(TranslationStackedInline):
    model = ProgramStat
    extra = 0
    fields = ('order', 'value', 'label')


class ProgramFaqItemInline(TranslationStackedInline):
    model = ProgramFaqItem
    extra = 0
    fields = ('order', 'question', 'answer')


@admin.register(ProgramPage)
class ProgramPageAdmin(RegionScopedAdminMixin, TabbedTranslationAdmin):
    list_display = ('region', 'hero_title', 'updated_at')
    readonly_fields = ('updated_at',)
    inlines = [
        ProgramAudienceItemInline,
        ProgramBenefitItemInline,
        ProgramVariantCardInline,
        ProgramTeamMemberInline,
        ProgramCertificateFeatureInline,
        ProgramStatInline,
        ProgramFaqItemInline,
    ]
    fieldsets = (
        (None, {'fields': ('region', 'updated_at')}),
        ('Hero', {
            'fields': (
                'hero_badge_text',
                'hero_title',
                'hero_subtitle',
                'hero_cta_primary_text',
                'hero_cta_secondary_text',
            ),
        }),
        ('Секция «Кому подходит»', {
            'fields': (
                'audience_label', 'audience_title', 'audience_subtitle',
                'audience_photo_woman', 'audience_photo_library',
            ),
        }),
        ('Секция «Что получает»', {
            'fields': (
                'benefits_label', 'benefits_title', 'benefits_subtitle',
                'benefits_photo_kid',
            ),
        }),
        ('Секция «Программы»', {
            'fields': ('programs_label', 'programs_title', 'programs_subtitle', 'programs_cta_text'),
        }),
        ('Секция «Команда»', {
            'fields': ('team_label', 'team_title', 'team_subtitle'),
        }),
        ('Секция «Аттестат»', {
            'fields': (
                'certificate_label', 'certificate_title', 'certificate_subtitle',
                'certificate_preview_image', 'certificate_cta_text',
            ),
        }),
        ('Секция «Внеклассные»', {
            'fields': (
                'activities_label', 'activities_title', 'activities_subtitle',
                'activities_cta_text',
            ),
        }),
        ('Секция «В цифрах»', {
            'fields': (
                'stats_label', 'stats_title', 'stats_intro_text', 'stats_photo',
            ),
        }),
        ('Секция «FAQ»', {
            'fields': ('faq_label', 'faq_title'),
        }),
    )
