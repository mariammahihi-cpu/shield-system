from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserBrowserSession


# ============================================================================
# 🔐 CUSTOM USER ADMIN - لوحة تحكم المستخدمين المخصصة
# ============================================================================

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):  # التعديل: الوراثة من BaseUserAdmin لحماية معالجة حقل كلمة المرور تلقائياً
    """
    لوحة تحكم مخصصة لإدارة المستخدمين مع مراقبة الأمان.
    """

    # ============================================================================
    # 📋 LIST DISPLAY - الأعمدة المعروضة في القائمة
    # ============================================================================
    list_display = (
        'username',
        'full_name',
        'email',
        'role_colored',
        'login_attempts_display',
        'is_locked_display',
        'is_active_display',
        'phone_number',
        'last_login',
    )

    # ============================================================================
    # 🔍 LIST FILTER - مرشحات سريعة
    # ============================================================================
    list_filter = (
        'role',
        'is_active',
        'is_locked',
        'is_superuser',
        'login_attempts',  # التعديل: فلتر مدمج قياسي لمنع انهيار السيرفر بسبب مكتبات خارجية غير مثبتة
        'date_joined',
        'last_login',
    )

    # ============================================================================
    # 🔎 SEARCH FIELDS - حقول البحث
    # ============================================================================
    search_fields = (
        'username',
        'full_name',
        'email',
        'phone_number',
    )

    # ============================================================================
    # 📑 FIELDSETS - تنظيم الحقول في صفحة التحرير
    # ============================================================================
    fieldsets = (
        ('🔐 بيانات المصادقة', {
            'fields': ('username', 'email'),  # التعديل: إزالة حقل كلمة المرور من العرض المباشر لحمايته، دجانجو سيعرض رابط التغيير الآمن بالأعلى تلقائياً
            'description': 'معلومات تسجيل الدخول الأساسية'
        }),
        ('👤 المعلومات الشخصية', {
            'fields': ('full_name', 'phone_number'),
            'description': 'البيانات الشخصية للمستخدم'
        }),
        ('🎖️ الدور والصلاحيات', {
            'fields': ('role', 'is_active', 'is_superuser', 'is_staff', 'groups', 'user_permissions'),
            'description': 'تحديد الدور والصلاحيات'
        }),
        ('🚨 أمان الحساب', {
            'fields': ('is_locked', 'login_attempts'),
            'classes': ('collapse', 'warning'),
            'description': 'معلومات الأمان والحسابات المقفولة'
        }),
        ('📅 معلومات النظام', {
            'fields': ('date_joined', 'last_login'),
            'classes': ('collapse',),
            'description': 'التواريخ والأوقات الأساسية'
        }),
    )

    ordering = ('-date_joined',)

    actions = [
        'unlock_accounts',
        'reset_login_attempts',
        'activate_users',
        'deactivate_users',
    ]

    # ============================================================================
    # 🎨 DISPLAY METHODS - دوال عرض مخصصة مع ألوان وأيقونات
    # ============================================================================

    def role_colored(self, obj):
        color_map = {
            'admin': '#e74c3c',
            'manager': '#3498db',
            'auditor': '#f39c12',
            'dispatcher': '#27ae60',
            'agent': '#9b59b6',
        }
        color = color_map.get(obj.role, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_role_display()
        )
    role_colored.short_description = '🎖️ الدور'

    def login_attempts_display(self, obj):
        attempts = obj.login_attempts
        if attempts == 0:
            return format_html('<span style="color: green; font-weight: bold;">✓ آمن</span>')
        elif attempts < 5:
            return format_html('<span style="color: orange; font-weight: bold;">⚠️ {}/5</span>', attempts)
        else:
            return format_html('<span style="color: red; font-weight: bold;">🚨 محظور</span>')
    login_attempts_display.short_description = '🔐 محاولات الدخول'

    def is_locked_display(self, obj):
        if obj.is_locked:
            return format_html('<span style="color: red; font-weight: bold;">🔒 مقفول</span>')
        else:
            return format_html('<span style="color: green; font-weight: bold;">🔓 مفتوح</span>')
    is_locked_display.short_description = '🔐 حالة القفل'

    def is_active_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green; font-weight: bold;">✓ نشط</span>')
        else:
            return format_html('<span style="color: red; font-weight: bold;">✗ غير نشط</span>')
    is_active_display.short_description = '✓ الحالة'

    # ============================================================================
    # 🎬 ACTION METHODS - تنفيذ الإجراءات الإدارية
    # ============================================================================

    def unlock_accounts(self, request, queryset):
        updated = 0
        for user in queryset.filter(is_locked=True):
            user.unlock_account()
            updated += 1
        self.message_user(request, f'✓ تم فتح {updated} حساب مقفول.')
    unlock_accounts.short_description = '🔓 فتح الحسابات المقفولة'

    def reset_login_attempts(self, request, queryset):
        updated = 0
        for user in queryset:
            user.reset_login_attempts()
            updated += 1
        self.message_user(request, f'✓ تم إعادة تعيين محاولات الدخول لـ {updated} مستخدم.')
    reset_login_attempts.short_description = '🔄 إعادة تعيين المحاولات'

    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'✓ تم تفعيل {updated} حساب.')
    activate_users.short_description = '✓ تفعيل الحسابات'

    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'✓ تم إلغاء تفعيل {updated} حساب.')
    deactivate_users.short_description = '✗ إلغاء تفعيل الحسابات'

    readonly_fields = ('date_joined', 'last_login', 'login_attempts')


# ============================================================================
# 🌐 USER BROWSER SESSION ADMIN - لوحة تحكم جلسات المتصفح
# ============================================================================

@admin.register(UserBrowserSession)
class UserBrowserSessionAdmin(admin.ModelAdmin):
    """
    لوحة تحكم جلسات المتصفح - لمراقبة وإدارة الجلسات المريبة.
    """
    list_display = (
        'user',
        'browser_fingerprint_short',
        'user_agent_short',
        'is_trusted_display',
        'created_at',
        'last_used_at',
    )

    list_filter = (
        'is_trusted',
        'created_at',
        'last_used_at',
    )

    search_fields = (
        'user__username',
        'user__full_name',
        'browser_fingerprint',
        'user_agent',
    )

    fieldsets = (
        ('👤 المستخدم', {
            'fields': ('user',),
            'description': 'المستخدم المرتبط بهذه الجلسة'
        }),
        ('🌐 معلومات المتصفح', {
            'fields': ('browser_fingerprint', 'user_agent'),
            'description': 'بيانات تحديد المتصفح'
        }),
        ('🔐 حالة الثقة', {
            'fields': ('is_trusted',),
            'description': 'هل هذا المتصفح موثوق'
        }),
        ('📅 التواريخ', {
            'fields': ('created_at', 'last_used_at'),
            'classes': ('collapse',),
            'description': 'معلومات الأوقات'
        }),
    )

    ordering = ('-last_used_at',)

    actions = [
        'mark_as_trusted',
        'mark_as_suspicious',
    ]

    def browser_fingerprint_short(self, obj):
        fp = obj.browser_fingerprint[:10] + '...' if obj.browser_fingerprint else ''
        return format_html(
            '<code style="background-color: #f0f0f0; padding: 5px; border-radius: 3px;">{}</code>',
            fp
        )
    browser_fingerprint_short.short_description = '🔑 البصمة'

    def user_agent_short(self, obj):
        if not obj.user_agent:
            return ''
        ua = obj.user_agent[:50]
        if len(obj.user_agent) > 50:
            ua += '...'
        return ua
    user_agent_short.short_description = '🌐 المتصفح'

    def is_trusted_display(self, obj):
        if obj.is_trusted:
            return format_html('<span style="color: green; font-weight: bold;">✓ موثوق</span>')
        else:
            return format_html('<span style="color: red; font-weight: bold;">⚠️ مريب</span>')
    is_trusted_display.short_description = '🔐 الثقة'

    def mark_as_trusted(self, request, queryset):
        updated = 0
        for session in queryset:
            session.mark_as_trusted()
            updated += 1
        self.message_user(request, f'✓ تم وضع علامة على {updated} جلسة كموثوقة.')
    mark_as_trusted.short_description = '✓ وضع علامة موثوقة'

    def mark_as_suspicious(self, request, queryset):
        updated = 0
        for session in queryset:
            session.mark_as_suspicious()
            updated += 1
        self.message_user(request, f'✓ تم وضع علامة على {updated} جلسة كمريبة.')
    mark_as_suspicious.short_description = '⚠️ وضع علامة مريبة'

    readonly_fields = ('created_at', 'last_used_at')

    def has_delete_permission(self, request, obj=None):  # التعديل: إضافة اختيارات الـ Arguments وإصلاح القوس الزائد
        """السماح بالحذف فقط للـ Superuser."""
        return request.user.is_superuser