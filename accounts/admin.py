from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Регион', {'fields': ('manager_region',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Регион', {'fields': ('manager_region',)}),
    )
    list_display = BaseUserAdmin.list_display + ('manager_region',)
    list_filter = BaseUserAdmin.list_filter + ('manager_region',)
    autocomplete_fields = ['manager_region']
