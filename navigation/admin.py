from django.contrib import admin
from modeltranslation.admin import TabbedTranslationAdmin, TranslationTabularInline

from .models import NavItem, NavSection


class NavItemInline(TranslationTabularInline):
    model = NavItem
    extra = 1
    fields = ('order', 'slug', 'label', 'url_name', 'flat_page', 'is_top_nav', 'is_published')
    ordering = ('order', 'pk')
    autocomplete_fields = ('flat_page',)


@admin.register(NavSection)
class NavSectionAdmin(TabbedTranslationAdmin):
    """Секции мегаменю редактируются вместе со своими пунктами (inline)."""

    list_display = ('label', 'slug', 'order', 'item_count')
    fields = ('slug', 'label', 'order')
    inlines = [NavItemInline]
    ordering = ('order', 'slug')

    @admin.display(description='Пунктов')
    def item_count(self, obj):
        return obj.items.count()

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(NavItem)
class NavItemAdmin(TabbedTranslationAdmin):
    """Отдельная регистрация — чтобы быстро находить пункт по slug/url_name."""

    list_display = ('label', 'slug', 'section', 'url_name', 'flat_page', 'is_top_nav', 'is_published', 'order')
    list_filter = ('section', 'is_top_nav', 'is_published')
    search_fields = ('slug', 'label', 'url_name')
    list_editable = ('order', 'is_top_nav', 'is_published')
    list_select_related = ('section', 'flat_page')
    autocomplete_fields = ('flat_page',)
    fields = ('section', 'slug', 'label', 'url_name', 'flat_page', 'is_top_nav', 'order', 'is_published')

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
