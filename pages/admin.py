from django.contrib import admin
from django.utils.html import format_html
from modeltranslation.admin import TabbedTranslationAdmin, TranslationStackedInline, TranslationTabularInline

from regions.admin import RegionScopedAdminMixin

from .models import ContactsDepartment, ContactsPage, FlatPage, HomeGalleryImage, HomePage


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


class ContactsDepartmentInline(TranslationStackedInline):
    model = ContactsDepartment
    extra = 1
    fields = ('order', 'title', 'description', 'phone', 'email', 'hours')


@admin.register(ContactsPage)
class ContactsPageAdmin(RegionScopedAdminMixin, TabbedTranslationAdmin):
    list_display = ('region', 'office_name', 'updated_at')
    readonly_fields = ('updated_at',)
    inlines = [ContactsDepartmentInline]
    fieldsets = (
        (None, {'fields': ('region', 'updated_at')}),
        ('Вводный блок', {'fields': ('intro_title', 'intro_text')}),
        ('Офис', {
            'fields': ('office_name', 'office_address', 'office_hours'),
        }),
        ('Карта (Leaflet, CartoDB light_nolabels)', {
            'fields': ('latitude', 'longitude', 'map_zoom'),
        }),
    )


@admin.register(FlatPage)
class FlatPageAdmin(RegionScopedAdminMixin, TabbedTranslationAdmin):
    """Статичные контентные страницы (О нас, форма, питание, privacy и т.п.).

    Region-scope как у блога: менеджер видит только свой регион,
    суперадмин — все.
    """

    list_display = (
        'title',
        'slug',
        'region',
        'is_published',
        'updated_at',
        'cover_preview',
    )
    list_filter = ('region', 'is_published')
    list_editable = ('is_published',)
    list_select_related = ('region',)
    search_fields = ('title', 'slug', 'lead', 'content')
    ordering = ('region', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'cover_preview_large')
    fieldsets = (
        ('Основное', {
            'fields': ('region', 'slug', 'title', 'lead'),
        }),
        ('Обложка', {
            'fields': (
                'cover_image',
                'cover_preview_large',
                'cover_alt',
                'cover_caption',
            ),
        }),
        ('Содержимое', {
            'fields': ('content',),
        }),
        ('SEO & Social', {
            'fields': (
                'seo_title',
                'seo_description',
                'og_title',
                'og_description',
            ),
        }),
        ('Публикация', {
            'fields': (
                'is_published',
                ('created_at', 'updated_at'),
            ),
        }),
    )

    @admin.display(description='Обложка')
    def cover_preview(self, obj):
        if not obj.cover_image:
            return '—'
        return format_html(
            '<img src="{}" style="height:40px;width:64px;object-fit:cover;border-radius:4px;" />',
            obj.cover_image.url,
        )

    @admin.display(description='Превью обложки')
    def cover_preview_large(self, obj):
        if not obj.cover_image:
            return '—'
        return format_html(
            '<img src="{}" style="max-height:200px;max-width:360px;border-radius:6px;" />',
            obj.cover_image.url,
        )
