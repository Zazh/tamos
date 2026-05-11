from django.contrib import admin
from modeltranslation.admin import TabbedTranslationAdmin, TranslationTabularInline

from regions.admin import RegionScopedAdminMixin

from .models import HomeGalleryImage, HomePage


class HomeGalleryImageInline(TranslationTabularInline):
    model = HomeGalleryImage
    extra = 1
    fields = ('order', 'image', 'alt_text')


@admin.register(HomePage)
class HomePageAdmin(RegionScopedAdminMixin, TabbedTranslationAdmin):
    list_display = ('region', 'hero_title', 'updated_at')
    readonly_fields = ('updated_at',)
    inlines = [HomeGalleryImageInline]
    fieldsets = (
        (None, {'fields': ('region', 'updated_at')}),
        ('Hero', {
            'fields': (
                'hero_image',
                'hero_badge_text',
                'hero_title',
                'hero_subtitle',
                'hero_cta_primary_text',
                'hero_cta_secondary_text',
            ),
        }),
        ('О нас', {
            'fields': ('about_label', 'about_title', 'about_body'),
        }),
        ('Видео', {
            'fields': ('video_file',),
        }),
    )
