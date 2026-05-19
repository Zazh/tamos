from django.contrib import admin
from django.utils.html import format_html
from modeltranslation.admin import TabbedTranslationAdmin

from regions.admin import RegionScopedAdminMixin

from .models import Album, GalleryCategory, GalleryImage


@admin.register(GalleryCategory)
class GalleryCategoryAdmin(TabbedTranslationAdmin):
    list_display = ('name', 'slug', 'order', 'is_published')
    list_editable = ('order', 'is_published')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'slug')
    ordering = ('order', 'name')


@admin.register(Album)
class AlbumAdmin(RegionScopedAdminMixin, TabbedTranslationAdmin):
    list_display = (
        'title',
        'region',
        'category',
        'photo_count',
        'is_published',
        'created_at',
    )
    list_filter = ('region', 'category', 'is_published')
    list_select_related = ('region', 'category')
    search_fields = ('title', 'slug', 'lead')
    ordering = ('-created_at',)
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'cover_preview_large')
    fieldsets = (
        ('Основное', {
            'fields': (
                ('region', 'category'),
                'slug',
                'title',
                'lead',
                'is_published',
            ),
        }),
        ('Обложка', {
            'fields': (
                'cover_image',
                'cover_preview_large',
            ),
        }),
        ('Служебное', {
            'fields': (('created_at', 'updated_at'),),
        }),
    )

    @admin.display(description='Фото')
    def photo_count(self, obj):
        return obj.images.count()

    @admin.display(description='Превью обложки')
    def cover_preview_large(self, obj):
        if not obj.cover_image:
            return '—'
        return format_html(
            '<img src="{}" style="max-height:200px;max-width:360px;border-radius:6px;" />',
            obj.cover_image.url,
        )


@admin.register(GalleryImage)
class GalleryImageAdmin(TabbedTranslationAdmin):
    """Edit отдельной фотографии. Region/category — через album (read-only)."""

    list_display = (
        'preview',
        'album',
        'album_region',
        'album_category',
        'is_wide',
        'is_published',
        'created_at',
    )
    list_filter = ('album__region', 'album__category', 'is_published', 'is_wide')
    list_editable = ('is_published', 'is_wide')
    list_select_related = ('album', 'album__region', 'album__category')
    search_fields = ('alt', 'caption', 'album__title')
    readonly_fields = ('created_at', 'updated_at', 'preview_large')
    fieldsets = (
        ('Альбом', {
            'fields': ('album',),
        }),
        ('Изображение', {
            'fields': (
                'image',
                'preview_large',
                'alt',
                'caption',
            ),
        }),
        ('Параметры показа', {
            'fields': (('is_published', 'is_wide'),),
        }),
        ('Служебное', {
            'fields': (('created_at', 'updated_at'),),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('album__region', 'album__category')
        if not request.user.is_superuser and request.user.manager_region_id:
            qs = qs.filter(album__region_id=request.user.manager_region_id)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (
            db_field.name == 'album'
            and not request.user.is_superuser
            and request.user.manager_region_id
        ):
            kwargs['queryset'] = Album.objects.filter(
                region_id=request.user.manager_region_id,
            ).select_related('category')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.display(description='Регион')
    def album_region(self, obj):
        return obj.album.region if obj.album else '—'

    @admin.display(description='Тема')
    def album_category(self, obj):
        return obj.album.category if obj.album else '—'

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
