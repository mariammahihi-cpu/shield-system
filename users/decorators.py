import logging
from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse

# إعداد الـ Logger لتتبع المحاولات المشبوهة والأحداث الأمنية
logger = logging.getLogger(__name__)


# ============================================================================
# 🎯 HELPER FUNCTIONS - دوال مساعدة (تم نقلها للأعلى لسلامة الاستدعاء)
# ============================================================================

def get_client_ip(request):
    """
    الحصول على عنوان IP الفعلي للعميل مع معالجة الـ Proxies والـ Load Balancers.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
        return ip
    return request.META.get('REMOTE_ADDR', 'Unknown')


# ============================================================================
# 🔐 ROLE-BASED ACCESS CONTROL (RBAC) DECORATORS
# ============================================================================

def role_required(*allowed_roles):
    """
    ديكوريتور لحماية الـ Views بناءً على الأدوار الوظيفية لنظام Shield.

    الوظيفة:
    - التحقق من تسجيل دخول المستخدم.
    - تجاوز الفحص تلقائياً للمديرين (Admin) لمرونة الإدارة.
    - التحقق من أن دور المستخدم موجود ضمن الأدوار المسموحة.
    - تسجيل محاولات الوصول المشبوهة في الـ Logs.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # ✅ الحالة 1: التحقق من تسجيل الدخول
            if not request.user.is_authenticated:
                client_ip = get_client_ip(request)
                logger.warning(
                    f'🚫 محاولة وصول بدون تسجيل دخول من IP {client_ip} للـ View: {request.path}'
                )
                return redirect(f"{reverse('users:login')}?next={request.path}")

            # ✅ الحالة 2: تجاوز الفحص للمديرين (صلاحيات كاملة)
            if request.user.is_superuser or request.user.role == 'admin':
                logger.info(
                    f'✅ وصول مدير: {request.user.username} (Admin) للـ View: {request.path} - تم التجاوز التلقائي'
                )
                return view_func(request, *args, **kwargs)

            # ✅ الحالة 3: فحص دور المستخدم
            if request.user.role in allowed_roles:
                logger.info(
                    f'✅ وصول مصرح: {request.user.username} ({request.user.get_role_display()}) للـ View: {request.path}'
                )
                return view_func(request, *args, **kwargs)

            # ❌ الحالة 4: دور غير مسموح - تسجيل خرق أمني محتمل
            client_ip = get_client_ip(request)
            logger.warning(
                f'🚫 محاولة وصول غير مصرح: {request.user.username} ({request.user.get_role_display()}) من IP {client_ip} '
                f'للـ View: {request.path} - الأدوار المسموحة: {", ".join(allowed_roles)}'
            )

            # إرجاع صفحة 403 Forbidden مع رسالة تفصيلية منسقة
            error_message = (
                f'❌ غير مصرح لك بالوصول لهذه الصفحة!\n\n'
                f'معلومات الحساب:\n'
                f'• اسم المستخدم: {request.user.username}\n'
                f'• الدور الحالي: {request.user.get_role_display()}\n\n'
                f'الأدوار المسموحة:\n'
                f'• {chr(10).join(allowed_roles)}\n\n'
                f'إذا كنت تعتقد أن هذا خطأ، يرجى التواصل مع الإدارة.'
            )

            return HttpResponseForbidden(error_message.replace('\n', '<br>'))

        return wrapper
    return decorator


def permission_required(permission_name):
    """
    ديكوريتور للتحقق من صلاحيات نظام Django الافتراضي (Django Permissions System).
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # ✅ الحالة 1: التحقق من تسجيل الدخول
            if not request.user.is_authenticated:
                client_ip = get_client_ip(request)
                logger.warning(
                    f'🚫 محاولة وصول بدون تسجيل دخول من IP {client_ip} للـ View: {request.path}'
                )
                return redirect(f"{reverse('users:login')}?next={request.path}")

            # ✅ الحالة 2: فحص الصلاحية القياسية
            if request.user.has_perm(permission_name):
                logger.info(
                    f'✅ وصول مصرح: {request.user.username} يمتلك الصلاحية [{permission_name}] للـ View: {request.path}'
                )
                return view_func(request, *args, **kwargs)

            # ❌ الحالة 3: لا يمتلك الصلاحية
            client_ip = get_client_ip(request)
            logger.warning(
                f'🚫 محاولة وصول بدون صلاحية: {request.user.username} من IP {client_ip} - يحتاج الصلاحية [{permission_name}] للـ View: {request.path}'
            )

            error_message = (
                f'❌ لا تمتلك الصلاحية المطلوبة!\n\n'
                f'معلومات الحساب:\n'
                f'• اسم المستخدم: {request.user.username}\n\n'
                f'الصلاحية المطلوبة:\n'
                f'• {permission_name}\n\n'
                f'إذا كنت تعتقد أن هذا خطأ، يرجى التواصل مع المدير.'
            )

            return HttpResponseForbidden(error_message.replace('\n', '<br>'))

        return wrapper
    return decorator