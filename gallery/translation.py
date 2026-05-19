from modeltranslation.translator import TranslationOptions, register

from .models import Album, GalleryCategory, GalleryImage


@register(GalleryCategory)
class GalleryCategoryTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(Album)
class AlbumTranslationOptions(TranslationOptions):
    fields = ('title', 'lead')


@register(GalleryImage)
class GalleryImageTranslationOptions(TranslationOptions):
    fields = ('alt', 'caption')
