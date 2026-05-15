from django.contrib import admin
from django.utils.html import format_html
from modeltranslation.admin import TabbedTranslationAdmin

from regions.admin import RegionScopedAdminMixin

from .models import GalleryCategory, GalleryImage


@admin.register(GalleryCategory)
class GalleryCategoryAdmin(TabbedTranslationAdmin):
    list_display = ('name', 'slug', 'order', 'is_published')
    list_editable = ('order', 'is_published')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'slug')
    ordering = ('order', 'name')


@admin.register(GalleryImage)
class GalleryImageAdmin(RegionScopedAdminMixin, TabbedTranslationAdmin):
    list_display = (
        'preview',
        'region',
        'category',
        'is_wide',
        'order',
        'is_published',
        'created_at',
    )
    list_filter = ('region', 'category', 'is_published', 'is_wide')
    list_editable = ('order', 'is_published', 'is_wide')
    list_select_related = ('region', 'category')
    search_fields = ('alt', 'caption')
    readonly_fields = ('created_at', 'updated_at', 'preview_large')
    fieldsets = (
        ('Основное', {
            'fields': (
                'region',
                'category',
                ('is_published', 'is_wide', 'order'),
            ),
        }),
        ('Изображение', {
            'fields': (
                'image',
                'preview_large',
                'alt',
                'caption',
            ),
        }),
        ('Служебное', {
            'fields': (('created_at', 'updated_at'),),
        }),
    )

    @admin.display(description='Превью')
    def preview(self, obj):
        if not obj.image:
            return '—'
        return format_html(
            '<img src="{}" style="height:40px;width:64px;object-fit:cover;border-radius:4px;" />',
            obj.image.url,
        )

    @admin.display(description='Превью большое')
    def preview_large(self, obj):
        if not obj.image:
            return '—'
        return format_html(
            '<img src="{}" style="max-height:200px;max-width:360px;border-radius:6px;" />',
            obj.image.url,
        )
