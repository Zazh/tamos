from modeltranslation.translator import TranslationOptions, register

from .models import GalleryCategory, GalleryImage


@register(GalleryCategory)
class GalleryCategoryTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(GalleryImage)
class GalleryImageTranslationOptions(TranslationOptions):
    fields = ('alt', 'caption')
