from django.contrib import admin
from django.utils.html import format_html
from modeltranslation.admin import TabbedTranslationAdmin

from regions.admin import RegionScopedAdminMixin

from .models import TeamMember


@admin.register(TeamMember)
class TeamMemberAdmin(RegionScopedAdminMixin, TabbedTranslationAdmin):
    list_display = (
        'name',
        'role',
        'region',
        'order',
        'is_published',
        'is_featured',
        'photo_preview',
    )
    list_filter = (
        'region', 'is_published', 'is_featured',
        'teaches_primary', 'teaches_middle', 'teaches_senior', 'is_admin',
    )
    list_editable = ('order', 'is_published', 'is_featured')
    list_select_related = ('region',)
    search_fields = ('name', 'role', 'slug', 'meta')
    ordering = ('region', 'order')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at', 'photo_preview_large')
    fieldsets = (
        ('Основное', {
            'fields': (
                ('region', 'order'),
                'slug',
                'name',
                'role',
                'meta',
                ('teaches_primary', 'teaches_middle', 'teaches_senior'),
                'is_admin',
            ),
        }),
        ('Фото', {
            'fields': ('photo', 'photo_preview_large'),
        }),
        ('Анкета', {
            'fields': ('quote', 'bio', 'linkedin_url'),
        }),
        ('SEO / OG', {
            'classes': ('collapse',),
            'description': (
                'Пусто — fallback на «ФИО — Должность» (title) и начало '
                'биографии (description).'
            ),
            'fields': (
                'seo_title',
                'seo_description',
                'og_title',
                'og_description',
            ),
        }),
        ('Публикация', {
            'fields': (
                ('is_published', 'is_featured'),
                ('created_at', 'updated_at'),
            ),
        }),
    )

    @admin.display(description='Фото')
    def photo_preview(self, obj):
        if not obj.photo:
            return '—'
        return format_html(
            '<img src="{}" style="height:48px;width:48px;object-fit:cover;border-radius:50%;" />',
            obj.photo.url,
        )

    @admin.display(description='Превью фото')
    def photo_preview_large(self, obj):
        if not obj.photo:
            return '—'
        return format_html(
            '<img src="{}" style="max-height:220px;max-width:220px;border-radius:18px;" />',
            obj.photo.url,
        )
