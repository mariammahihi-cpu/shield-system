from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserDevice


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'full_name', 'role', 'phone_number', 'is_locked', 'login_attempts', 'is_active')
    list_filter  = ('role', 'is_locked', 'is_active')
    search_fields = ('username', 'full_name', 'phone_number')
    ordering = ('role', 'full_name')
    fieldsets = UserAdmin.fieldsets + (
        ('معلومات Shield', {'fields': ('full_name', 'role', 'phone_number', 'is_locked', 'login_attempts')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('معلومات Shield', {'fields': ('full_name', 'role', 'phone_number')}),
    )


@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_name', 'device_uuid', 'is_verified', 'bound_at', 'last_login_at')
    list_filter = ('is_verified', 'bound_at')
    search_fields = ('user__full_name', 'device_name', 'device_uuid')
    readonly_fields = ('device_uuid', 'bound_at')
    ordering = ('-bound_at',)