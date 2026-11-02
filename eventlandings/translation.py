from modeltranslation.translator import TranslationOptions, register

from .models import (
    EventLanding,
    EventLandingDay,
    EventLandingGalleryImage,
    EventLandingMaterial,
    EventLandingProgramRow,
    EventLandingTile,
)


@register(EventLanding)
class EventLandingTranslationOptions(TranslationOptions):
    fields = (
        'title',
        'badge_text',
        'lead',
        'audience_title',
        'audience_text',
        'goal',
        'program_title',
        'materials_title',
        'leaders_title',
        'leaders_lead',
        'reg_title',
        'reg_text',
        'form_title',
        'form_lead',
        'form_note',
        'cta_text',
        'price_note',
        'seo_title',
        'seo_description',
        'og_title',
        'og_description',
    )


@register(EventLandingDay)
class EventLandingDayTranslationOptions(TranslationOptions):
    fields = ('label',)


@register(EventLandingProgramRow)
class EventLandingProgramRowTranslationOptions(TranslationOptions):
    fields = ('title', 'text')


@register(EventLandingMaterial)
class EventLandingMaterialTranslationOptions(TranslationOptions):
    fields = ('title',)


@register(EventLandingTile)
class EventLandingTileTranslationOptions(TranslationOptions):
    fields = ('title', 'text')


@register(EventLandingGalleryImage)
class EventLandingGalleryImageTranslationOptions(TranslationOptions):
    fields = ('alt_text',)
