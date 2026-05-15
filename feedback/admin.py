from django.contrib import admin

from regions.admin import RegionScopedAdminMixin

from .models import Lead


@admin.register(Lead)
class LeadAdmin(RegionScopedAdminMixin, admin.ModelAdmin):
    """Заявки. Менеджер региона видит только свои; superuser — все."""

    list_display = (
        'created_at',
        'status',
        'name',
        'phone',
        'city',
        'region',
        'category',
        'origin',
    )
    list_display_links = ('created_at', 'name')
    list_filter = ('status', 'category', 'region', 'created_at')
    list_editable = ('status',)
    list_select_related = ('region',)
    search_fields = ('name', 'phone', 'origin', 'title', 'manager_note', 'city')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'

    readonly_fields = (
        'created_at',
        'updated_at',
        'consented_at',
        'policy_version',
        'ip_address',
        'user_agent',
        'origin',
        'title',
        'name',
        'phone',
        'city',
    )

    fieldsets = (
        ('Заявка', {
            'fields': (
                ('region', 'category'),
                ('name', 'phone'),
                ('city', 'origin'),
                'title',
            ),
        }),
        ('Обработка', {
            'fields': ('status', 'manager_note'),
        }),
        ('Аудит', {
            'classes': ('collapse',),
            'fields': (
                ('created_at', 'updated_at'),
                ('consented_at', 'policy_version'),
                ('ip_address', 'user_agent'),
            ),
        }),
    )

    actions = ('mark_in_progress', 'mark_done', 'mark_rejected')

    @admin.action(description='Перевести в «В работе»')
    def mark_in_progress(self, request, queryset):
        updated = queryset.update(status=Lead.Status.IN_PROGRESS)
        self.message_user(request, f'Обновлено: {updated}')

    @admin.action(description='Закрыть успешно')
    def mark_done(self, request, queryset):
        updated = queryset.update(status=Lead.Status.DONE)
        self.message_user(request, f'Обновлено: {updated}')

    @admin.action(description='Отметить как отказ/спам')
    def mark_rejected(self, request, queryset):
        updated = queryset.update(status=Lead.Status.REJECTED)
        self.message_user(request, f'Обновлено: {updated}')

    def has_add_permission(self, request):
        # Заявки создаются только через публичную форму, не в админке.
        return False

    def has_delete_permission(self, request, obj=None):
        # Историю заявок не удаляем — суперадмин при необходимости
        # делает это через shell/SQL.
        return request.user.is_superuser
