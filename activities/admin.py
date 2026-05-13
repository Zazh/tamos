from django.contrib import admin
from modeltranslation.admin import TabbedTranslationAdmin, TranslationStackedInline, TranslationTabularInline

from regions.admin import RegionScopedAdminMixin

from .models import Activity, ActivityGroup, ActivitySection, ScheduleSlot, Teacher


@admin.register(ActivitySection)
class ActivitySectionAdmin(TabbedTranslationAdmin):
    """Секции глобальные — только суперадмин."""

    list_display = ('order', 'slug', 'title')
    list_display_links = ('slug', 'title')
    list_editable = ('order',)
    ordering = ('order', 'slug')
    fields = ('slug', 'title', 'order')

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


@admin.register(Teacher)
class TeacherAdmin(RegionScopedAdminMixin, TabbedTranslationAdmin):
    list_display = ('name', 'phone_display', 'region', 'order')
    list_filter = ('region',)
    search_fields = ('name', 'phone', 'phone_display')
    ordering = ('order', 'name')
    fields = ('region', 'name', 'phone_display', 'phone', 'bio', 'photo', 'order')


class ScheduleSlotInline(admin.TabularInline):
    model = ScheduleSlot
    extra = 0
    fields = ('order', 'day', 'start_time', 'end_time')


@admin.register(ActivityGroup)
class ActivityGroupAdmin(TabbedTranslationAdmin):
    """Группы редактируются здесь (с inline-расписанием).

    Регион-скоп через связанную Activity: фильтруем queryset, ограничиваем
    выбор FK activity. Без RegionScopedAdminMixin — нет прямого region FK.
    """

    list_display = ('label', 'activity', 'students_status', 'price', 'order')
    list_filter = ('activity__region', 'students_status', 'activity__section')
    search_fields = ('label', 'activity__name')
    ordering = ('activity', 'order')
    inlines = [ScheduleSlotInline]
    fields = (
        'activity',
        'label',
        'classes',
        'price',
        'students_status',
        ('min_students', 'max_students'),
        'order',
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.manager_region_id is None:
            return qs.none()
        return qs.filter(activity__region_id=request.user.manager_region_id)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (
            db_field.name == 'activity'
            and not request.user.is_superuser
            and request.user.manager_region_id
        ):
            kwargs['queryset'] = Activity.objects.filter(region_id=request.user.manager_region_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ActivityGroupInline(TranslationStackedInline):
    """Inline-предпросмотр групп на странице кружка.

    Расписание тут НЕ редактируется (нужна вложенность 2 уровня — Django не
    поддерживает). Менеджер открывает группу отдельно через ActivityGroupAdmin,
    чтобы добавить/изменить слоты расписания.
    """

    model = ActivityGroup
    extra = 0
    fields = (
        'order',
        'label',
        'classes',
        'price',
        'students_status',
        ('min_students', 'max_students'),
    )
    show_change_link = True


@admin.register(Activity)
class ActivityAdmin(RegionScopedAdminMixin, TabbedTranslationAdmin):
    list_display = ('name', 'section', 'region', 'teacher', 'is_featured', 'is_published', 'order')
    list_filter = ('region', 'section', 'is_featured', 'is_published')
    list_editable = ('is_featured', 'is_published', 'order')
    search_fields = ('name', 'description', 'location')
    ordering = ('section', 'order', 'name')
    inlines = [ActivityGroupInline]
    fields = (
        ('region', 'section'),
        'teacher',
        'name',
        'description',
        'location',
        ('is_featured', 'is_published', 'order'),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Тренеры тоже регион-скопе: менеджер Астаны выбирает только астанинских.
        if (
            db_field.name == 'teacher'
            and not request.user.is_superuser
            and request.user.manager_region_id
        ):
            kwargs['queryset'] = Teacher.objects.filter(region_id=request.user.manager_region_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
