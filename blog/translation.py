from modeltranslation.translator import TranslationOptions, register

from .models import BlogCategory, BlogGalleryImage, BlogPost, BlogTag


@register(BlogCategory)
class BlogCategoryTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(BlogTag)
class BlogTagTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(BlogPost)
class BlogPostTranslationOptions(TranslationOptions):
    fields = ('title', 'lead', 'content', 'cover_caption', 'cover_alt')


@register(BlogGalleryImage)
class BlogGalleryImageTranslationOptions(TranslationOptions):
    fields = ('caption', 'alt')
