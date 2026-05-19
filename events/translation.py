from modeltranslation.translator import TranslationOptions, register

from .models import Event, EventGalleryImage


@register(Event)
class EventTranslationOptions(TranslationOptions):
    fields = (
        'title',
        'lead',
        'content',
        'cover_caption',
        'cover_alt',
        'seo_title',
        'seo_description',
        'og_title',
        'og_description',
    )


@register(EventGalleryImage)
class EventGalleryImageTranslationOptions(TranslationOptions):
    fields = ('caption', 'alt')
