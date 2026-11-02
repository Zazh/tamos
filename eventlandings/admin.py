from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from modeltranslation.admin import TabbedTranslationAdmin, TranslationTabularInline

from regions.admin import RegionScopedAdminMixin
from team.models import TeamMember

from .models import (
    EventLanding,
    EventLandingDay,
    EventLandingGalleryImage,
    EventLandingMaterial,
    EventLandingProgramRow,
    EventLandingTile,
)


class EventLandingDayInline(TranslationTabularInline):
    model = EventLandingDay
    extra = 0
    fields = ('date', 'start', 'end', 'label', 'program_link')
    readonly_fields = ('program_link',)

    @admin.display(description='Программа')
    def program_link(self, obj):
        if not obj.pk:
            return '—'
        url = reverse('admin:eventlandings_eventlandingday_change', args=[obj.pk])
        return format_html('<a href="{}">→ строки программы ({})</a>', url, obj.rows.count())


class EventLandingMaterialInline(TranslationTabularInline):
    model = EventLandingMaterial
    extra = 0
    fields = ('order', 'title')


class EventLandingTileInline(TranslationTabularInline):
    model = EventLandingTile
    extra = 0
    fields = ('order', 'title', 'text')


class EventLandingGalleryImageInline(TranslationTabularInline):
    model = EventLandingGalleryImage
    extra = 0
    fields = ('order', 'image', 'orientation', 'alt_text')
    readonly_fields = ('orientation',)


@admin.register(EventLanding)
class EventLandingAdmin(RegionScopedAdminMixin, TabbedTranslationAdmin):
    list_display = ('title', 'region', 'is_published', 'is_paid', 'price')
    list_filter = ('region', 'is_published')
    list_select_related = ('region',)
    search_fields = ('title', 'slug', 'lead')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('leaders',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [
        EventLandingDayInline,
        EventLandingTileInline,
        EventLandingMaterialInline,
        EventLandingGalleryImageInline,
    ]
    fieldsets = (
        ('Основное', {
            'fields': ('region', 'slug', 'is_published', 'title', 'badge_text', 'lead'),
        }),
        ('Цена и форма', {
            'fields': (
                ('is_paid', 'price'),
                'price_note',
                'cta_text',
                'show_parent_checkbox',
                'form_title',
                'form_lead',
                'form_note',
            ),
        }),
        ('Для кого', {
            'fields': ('audience_title', 'audience_text', 'goal'),
        }),
        ('Программа и материалы', {
            'fields': ('program_title', 'materials_title'),
        }),
        ('Ведущие', {
            'fields': ('leaders_title', 'leaders_lead', 'leaders'),
        }),
        ('Регистрация', {
            'fields': ('reg_title', 'reg_text'),
        }),
        ('SEO & Social', {
            'fields': ('seo_title', 'seo_description', 'og_title', 'og_description'),
        }),
        ('Служебное', {
            'fields': (('created_at', 'updated_at'),),
        }),
    )

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'leaders':
            obj_id = request.resolver_match.kwargs.get('object_id') if request.resolver_match else None
            landing = EventLanding.objects.filter(pk=obj_id).only('region_id').first() if obj_id else None
            if landing is not None:
                kwargs['queryset'] = TeamMember.objects.filter(region_id=landing.region_id)
        return super().formfield_for_manytomany(db_field, request, **kwargs)


class EventLandingProgramRowInline(TranslationTabularInline):
    model = EventLandingProgramRow
    extra = 0
    fields = ('order', 'start', 'duration_min', 'title', 'text', 'is_break')


@admin.register(EventLandingDay)
class EventLandingDayAdmin(TabbedTranslationAdmin):
    """Строки программы дня (вложенные inline Django не умеет — отдельная страница)."""

    list_display = ('__str__', 'date', 'start', 'end')
    list_filter = ('landing__region',)
    list_select_related = ('landing',)
    fields = ('landing', 'date', 'start', 'end', 'label')
    inlines = [EventLandingProgramRowInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('landing', 'landing__region')
        if not request.user.is_superuser:
            if request.user.manager_region_id is None:
                return qs.none()
            qs = qs.filter(landing__region_id=request.user.manager_region_id)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (
            db_field.name == 'landing'
            and not request.user.is_superuser
            and request.user.manager_region_id
        ):
            kwargs['queryset'] = EventLanding.objects.filter(
                region_id=request.user.manager_region_id,
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
