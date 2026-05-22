from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from modeltranslation.admin import TabbedTranslationAdmin, TranslationStackedInline

from regions.admin import RegionScopedAdminMixin

from .models import Event, EventGallery, EventGalleryImage


class EventGalleryInline(admin.TabularInline):
    """Список галерей внутри события. Картинки редактируются на отдельной
    странице галереи (вложенные inlines Django не поддерживает нативно)."""

    model = EventGallery
    extra = 0
    fields = ('order', 'slug', 'title', 'image_count', 'edit_link')
    readonly_fields = ('image_count', 'edit_link')
    show_change_link = True

    @admin.display(description='Фото')
    def image_count(self, obj):
        if not obj.pk:
            return '—'
        return obj.images.count()

    @admin.display(description='Открыть')
    def edit_link(self, obj):
        if not obj.pk:
            return format_html('<em>сохраните событие и нажмите «✏» справа</em>')
        url = reverse('admin:events_eventgallery_change', args=[obj.pk])
        return format_html('<a href="{}">→ редактировать фото</a>', url)


class EventGalleryImageInline(TranslationStackedInline):
    model = EventGalleryImage
    extra = 0
    fields = ('order', 'image', 'caption', 'alt')


@admin.register(EventGallery)
class EventGalleryAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'event', 'slug', 'image_count')
    list_filter = ('event__region',)
    search_fields = ('title', 'slug', 'event__title')
    inlines = [EventGalleryImageInline]
    fields = ('event', 'slug', 'title', 'order')

    @admin.display(description='Фото')
    def image_count(self, obj):
        return obj.images.count()

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('event', 'event__region')
        if not request.user.is_superuser and request.user.manager_region_id:
            qs = qs.filter(event__region_id=request.user.manager_region_id)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (
            db_field.name == 'event'
            and not request.user.is_superuser
            and request.user.manager_region_id
        ):
            kwargs['queryset'] = Event.objects.filter(
                region_id=request.user.manager_region_id,
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


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
    inlines = [EventGalleryInline]
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
            'description': (
                'Чтобы вставить дополнительную фотогалерею, добавьте её ниже '
                '(раздел «Фотогалереи») и поставьте в тексте шорткод '
                '<code>[[gallery slug=ИМЯ]]</code> — он заменится каруселью.'
            ),
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
