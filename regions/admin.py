from django.contrib import admin

from .models import Region


class RegionScopedAdminMixin:
    """
    Подмешать в любой ModelAdmin, у модели которого есть FK `region`.
    Суперадмин видит всё; пользователь с `manager_region` видит только свой регион,
    у него поле `region` в форме автозаполняется и не редактируется.

    Имя FK можно переопределить через `region_field`.
    """
    region_field = 'region'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.manager_region_id is None:
            return qs.none()
        return qs.filter(**{self.region_field: request.user.manager_region})

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        if not request.user.is_superuser and request.user.manager_region_id:
            initial[self.region_field] = request.user.manager_region_id
        return initial

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (
            db_field.name == self.region_field
            and not request.user.is_superuser
            and request.user.manager_region_id
        ):
            kwargs['queryset'] = Region.objects.filter(pk=request.user.manager_region_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_change_permission(self, request, obj=None):
        if obj is not None and not request.user.is_superuser and request.user.manager_region_id:
            if getattr(obj, f'{self.region_field}_id') != request.user.manager_region_id:
                return False
        return super().has_change_permission(request, obj=obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and not request.user.is_superuser and request.user.manager_region_id:
            if getattr(obj, f'{self.region_field}_id') != request.user.manager_region_id:
                return False
        return super().has_delete_permission(request, obj=obj)


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('slug', 'name', 'is_default', 'phone')
    list_filter = ('is_default',)
    search_fields = ('slug', 'name', 'name_ru', 'name_kk', 'name_en')
    fields = ('slug', 'is_default', 'name', 'phone', 'address')

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
