from django.contrib import admin
from django.utils.html import format_html
from modeltranslation.admin import TabbedTranslationAdmin

from regions.admin import RegionScopedAdminMixin

from .models import Event


@admin.register(Event)
class EventAdmin(RegionScopedAdminMixin, TabbedTranslationAdmin):
    list_display = (
        'title',
        'region',
        'is_published',
        'published_at',
        'cover_preview',
    )
    list_filter = ('region', 'is_published')
    list_editable = ('is_published',)
    list_select_related = ('region',)
    search_fields = ('title', 'lead', 'content', 'slug')
    ordering = ('-published_at',)
    date_hierarchy = 'published_at'
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'cover_preview_large')
    fieldsets = (
        ('Основное', {
            'fields': (
                'region',
                'slug',
                'title',
                'lead',
            ),
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
        ('Публикация', {
            'fields': (
                ('is_published', 'published_at'),
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
