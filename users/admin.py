from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User # تأكدي من اسم الموديل عندكِ لو كان CustomUser أو User

class CustomUserAdmin(UserAdmin):
    # الحقول التي تظهر عند تعديل بيانات مستخدم موجود مسبقاً
    fieldsets = UserAdmin.fieldsets + (
        ('بيانات Shield المخصصة', {
            'fields': ('role', 'phone_number', 'warehouse', 'station', 'login_attempts', 'is_locked')
        }),
    )
    # الحقول التي تظهر عند إنشاء مستخدم جديد لأول مرة
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('بيانات Shield المخصصة', {
            'fields': ('role', 'phone_number', 'warehouse', 'station')
        }),
    )

admin.site.register(User, CustomUserAdmin)