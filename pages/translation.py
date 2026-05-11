from modeltranslation.translator import TranslationOptions, register

from .models import HomeGalleryImage, HomePage


@register(HomePage)
class HomePageTranslationOptions(TranslationOptions):
    fields = (
        'hero_badge_text',
        'hero_title',
        'hero_subtitle',
        'hero_cta_primary_text',
        'hero_cta_secondary_text',
        'about_label',
        'about_title',
        'about_body',
    )


@register(HomeGalleryImage)
class HomeGalleryImageTranslationOptions(TranslationOptions):
    fields = ('alt_text',)
