from django.contrib import admin
from modeltranslation.admin import TabbedTranslationAdmin, TranslationStackedInline, TranslationTabularInline

from regions.admin import RegionScopedAdminMixin
from regions.models import Region

from .models import (
    AdmissionDocument,
    AdmissionIncludedItem,
    AdmissionPage,
    AdmissionPricingPlan,
    AdmissionTestingFeature,
    AdmissionVariant,
    Department,
    GradeGroup,
)


# --- Глобальные справочники (только суперюзер) -------------------------

@admin.register(Department)
class DepartmentAdmin(TabbedTranslationAdmin):
    list_display = ('slug', 'name', 'order')
    list_editable = ('order',)
    ordering = ('order',)
    fields = ('slug', 'name', 'order')

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


@admin.register(GradeGroup)
class GradeGroupAdmin(TabbedTranslationAdmin):
    list_display = ('slug', 'name', 'short_name', 'order')
    list_editable = ('order',)
    ordering = ('order',)
    fields = ('slug', 'name', 'short_name', 'order')

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


# --- Страница per region ----------------------------------------------

class AdmissionIncludedItemInline(TranslationStackedInline):
    model = AdmissionIncludedItem
    extra = 0
    fields = ('order', 'is_excluded', 'text')


class AdmissionDocumentInline(TranslationStackedInline):
    model = AdmissionDocument
    extra = 0
    fields = ('order', 'text')


@admin.register(AdmissionPage)
class AdmissionPageAdmin(RegionScopedAdminMixin, TabbedTranslationAdmin):
    list_display = ('region', 'updated_at')
    readonly_fields = ('updated_at',)
    inlines = [AdmissionIncludedItemInline, AdmissionDocumentInline]
    fieldsets = (
        (None, {'fields': ('region', 'updated_at')}),
        ('UI-лейблы', {
            'fields': (
                'breadcrumb_root_label',
                'department_dropdown_label',
                'grade_dropdown_label',
            ),
        }),
        ('Stepper · этапы', {
            'description': 'Тексты в боковом stepper. Слева направо на мобиле / сверху вниз справа на десктопе.',
            'fields': (
                'stage_consultation_title', 'stage_consultation_meta',
                'stage_testing_title', 'stage_testing_meta',
                'stage_result_title', 'stage_result_meta',
                'stage_contract_title', 'stage_contract_meta',
                'stage_enrollment_title', 'stage_enrollment_meta',
            ),
        }),
        ('Заголовки секций (h3)', {
            'fields': (
                'testing_section_title',
                'result_section_title',
                'contract_section_title',
                'enrollment_section_title',
                'consultation_section_title',
            ),
        }),
        ('Этап «Тестирование» — общая часть', {
            'fields': (
                'testing_rules_text',
                'testing_price_label',
                'testing_price_value',
            ),
        }),
        ('Этап «Договор и взнос» — общая часть', {
            'fields': (
                'enrollment_fee_text',
                'pricing_included_title',
                'pricing_excluded_title',
            ),
        }),
        ('Этап «Зачисление»', {
            'fields': (
                'enrollment_lead',
                'documents_title',
            ),
        }),
        ('Этап «Консультация»', {
            'fields': (
                'consultation_lead',
                'consultation_cta_text',
            ),
        }),
    )


# --- Variant per (page, dept, grade) -----------------------------------

class AdmissionTestingFeatureInline(TranslationStackedInline):
    model = AdmissionTestingFeature
    extra = 0
    fields = ('order', 'title', 'description', 'icon_svg')


class AdmissionPricingPlanInline(TranslationStackedInline):
    model = AdmissionPricingPlan
    extra = 0
    fields = (
        'order', 'highlight', 'badge_text', 'label',
        'price_value', 'price_currency', 'note', 'icon_svg',
    )


@admin.register(AdmissionVariant)
class AdmissionVariantAdmin(TabbedTranslationAdmin):
    """Region-scoping через page__region (Mixin поддерживает только прямой FK,
    поэтому фильтрация и permissions переопределены здесь явно)."""

    list_display = ('page', 'department', 'grade')
    list_filter = ('page__region', 'department', 'grade')
    list_select_related = ('page__region', 'department', 'grade')
    autocomplete_fields = ()
    inlines = [AdmissionTestingFeatureInline, AdmissionPricingPlanInline]
    fieldsets = (
        (None, {'fields': ('page', 'department', 'grade')}),
        ('Hero', {'fields': ('h1', 'hero_lead')}),
        ('Этап «Тестирование»', {'fields': ('testing_lead',)}),
        ('Этап «Результат»', {'fields': ('result_intro', 'result_detail')}),
        ('Этап «Договор и взнос»', {'fields': ('pricing_lead',)}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.manager_region_id is None:
            return qs.none()
        return qs.filter(page__region_id=request.user.manager_region_id)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (
            db_field.name == 'page'
            and not request.user.is_superuser
            and request.user.manager_region_id
        ):
            kwargs['queryset'] = AdmissionPage.objects.filter(
                region_id=request.user.manager_region_id
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_change_permission(self, request, obj=None):
        if obj and not request.user.is_superuser and request.user.manager_region_id:
            if obj.page.region_id != request.user.manager_region_id:
                return False
        return super().has_change_permission(request, obj=obj)

    def has_delete_permission(self, request, obj=None):
        if obj and not request.user.is_superuser and request.user.manager_region_id:
            if obj.page.region_id != request.user.manager_region_id:
                return False
        return super().has_delete_permission(request, obj=obj)
