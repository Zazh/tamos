from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from modeltranslation.admin import TabbedTranslationAdmin, TranslationStackedInline

from regions.admin import RegionScopedAdminMixin

from .models import BlogCategory, BlogGallery, BlogGalleryImage, BlogPost, BlogTag


@admin.register(BlogCategory)
class BlogCategoryAdmin(RegionScopedAdminMixin, TabbedTranslationAdmin):
    list_display = ('name', 'slug', 'region', 'order')
    list_filter = ('region',)
    list_editable = ('order',)
    search_fields = ('name', 'slug')
    ordering = ('region', 'order', 'name')
    prepopulated_fields = {'slug': ('name',)}
    fields = ('region', 'slug', 'name', 'order')


@admin.register(BlogTag)
class BlogTagAdmin(RegionScopedAdminMixin, TabbedTranslationAdmin):
    list_display = ('name', 'slug', 'region', 'order')
    list_filter = ('region',)
    list_editable = ('order',)
    search_fields = ('name', 'slug')
    ordering = ('region', 'order', 'name')
    prepopulated_fields = {'slug': ('name',)}
    fields = ('region', 'slug', 'name', 'order')


class BlogGalleryInline(admin.TabularInline):
    """Список галерей внутри статьи: без вложенных инлайнов.

    Картинки добавляются на отдельной странице галереи (см. ссылку
    `edit_link`). Django не поддерживает nested inlines нативно — это
    самый простой и предсказуемый паттерн.
    """

    model = BlogGallery
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
            return format_html('<em>сохраните статью и нажмите «✏» справа</em>')
        url = reverse('admin:blog_bloggallery_change', args=[obj.pk])
        return format_html('<a href="{}">→ редактировать фото</a>', url)


class BlogGalleryImageInline(TranslationStackedInline):
    model = BlogGalleryImage
    extra = 0
    fields = ('order', 'image', 'caption', 'alt')


@admin.register(BlogGallery)
class BlogGalleryAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'post', 'slug', 'image_count')
    list_filter = ('post__region',)
    search_fields = ('title', 'slug', 'post__title')
    inlines = [BlogGalleryImageInline]
    fields = ('post', 'slug', 'title', 'order')

    @admin.display(description='Фото')
    def image_count(self, obj):
        return obj.images.count()

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('post', 'post__region')
        if not request.user.is_superuser and request.user.manager_region_id:
            qs = qs.filter(post__region_id=request.user.manager_region_id)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (
            db_field.name == 'post'
            and not request.user.is_superuser
            and request.user.manager_region_id
        ):
            kwargs['queryset'] = BlogPost.objects.filter(
                region_id=request.user.manager_region_id,
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(BlogPost)
class BlogPostAdmin(RegionScopedAdminMixin, TabbedTranslationAdmin):
    """Полное редактирование статьи. Регион-скоп через RegionScopedAdminMixin.

    Категории и теги тоже регион-скопе: менеджер Астаны выбирает только
    астанинские (см. formfield_for_*).
    """

    list_display = (
        'title',
        'category',
        'region',
        'is_published',
        'published_at',
        'cover_preview',
    )
    list_filter = ('region', 'category', 'is_published', 'tags')
    list_editable = ('is_published',)
    list_select_related = ('region', 'category')
    search_fields = ('title', 'lead', 'content', 'slug')
    ordering = ('-published_at',)
    date_hierarchy = 'published_at'
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('tags',)
    readonly_fields = ('created_at', 'updated_at', 'cover_preview_large')
    inlines = [BlogGalleryInline]
    fieldsets = (
        ('Основное', {
            'fields': (
                ('region', 'category'),
                'tags',
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
                'Чтобы вставить фотогалерею, добавьте её ниже (раздел «Фотогалереи»), '
                'затем поставьте в тексте шорткод <code>[[gallery slug=ИМЯ]]</code> '
                '— он заменится каруселью при показе.'
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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Категория — только из региона менеджера.
        if (
            db_field.name == 'category'
            and not request.user.is_superuser
            and request.user.manager_region_id
        ):
            kwargs['queryset'] = BlogCategory.objects.filter(
                region_id=request.user.manager_region_id,
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # Теги — только из региона менеджера.
        if (
            db_field.name == 'tags'
            and not request.user.is_superuser
            and request.user.manager_region_id
        ):
            kwargs['queryset'] = BlogTag.objects.filter(
                region_id=request.user.manager_region_id,
            )
        return super().formfield_for_manytomany(db_field, request, **kwargs)
