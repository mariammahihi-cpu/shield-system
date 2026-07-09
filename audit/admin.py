from django.contrib import admin
from .models import AdminAction, AuditLog


@admin.register(AdminAction)
class AdminActionAdmin(admin.ModelAdmin):
    list_display  = ('action_type', 'target_user', 'admin_user', 'is_active', 'created_at')
    list_filter   = ('action_type', 'is_active', 'created_at')
    search_fields = ('target_user__username', 'target_user__full_name', 'reason')
    readonly_fields = ('target_user', 'admin_user', 'action_type', 'reason', 'created_at')
    date_hierarchy  = 'created_at'

    def has_add_permission(self, request):      # لا إضافة يدوية
        return False
    def has_delete_permission(self, request, obj=None):  # لا حذف
        return False


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display  = ('action', 'target_table', 'target_id', 'user', 'ip_address', 'timestamp')
    list_filter   = ('action', 'target_table', 'timestamp')
    search_fields = ('action', 'target_table', 'user__username')
    readonly_fields = ('user', 'action', 'target_table', 'target_id',
                       'ip_address', 'old_value', 'new_value', 'timestamp')
    date_hierarchy  = 'timestamp'

    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):  # عرض فقط
        return False
    def has_delete_permission(self, request, obj=None):
        return False
