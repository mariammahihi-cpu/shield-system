from django.urls import path
from . import views

# تعريف الـ Namespace لضمان عمل الروابط العكسية (Reverse URLs)
# مثال الاستخدام: reverse('users:login') أو {% url 'users:profile' %}
app_name = 'users'


urlpatterns = [
    # ========================================================================
    # 🔐 [مجموعة المصادقة - Authentication]
    # ========================================================================

    # مسار تسجيل الدخول الآمن
    # يدعم GET (عرض الفورم) و POST (معالجة بيانات الدخول)
    # الحماية: Timing Attacks + Brute Force + Browser Fingerprinting
    path('login/', views.login_view, name='login'),

    # مسار تسجيل الخروج الآمن
    # محمي بـ @login_required و POST فقط (لمنع هجمات CSRF)
    # يقوم بتطهير الجلسة وحذف كوكي بصمة المتصفح
    path('logout/', views.logout_view, name='logout'),
    # ====== إدارة الحسابات (المدير) ======
    path('users/',                          views.user_list,         name='user_list'),
    path('users/create/',                   views.create_user,       name='create_user'),
    path('users/<int:user_id>/toggle-active/', views.toggle_active_user, name='toggle_active'),
    path('users/<int:user_id>/toggle-ban/',    views.toggle_ban_user,    name='toggle_ban'),
    path('devices/<int:session_id>/toggle-trust/', views.toggle_device_trust, name='toggle_device_trust'),
    # ========================================================================
    # 👤 [مجموعة الملف الشخصي - User Profile]
    # ========================================================================

    # مسار عرض الملف الشخصي للمستخدم
    # يعرض: بيانات الحساب + الدور + جلسات المتصفح الموثوقة
    path('profile/', views.profile_view, name='profile'),
    #يعرض الاعدادات التشغيلية
    path('settings/', views.system_settings, name='system_settings'),


    # ========================================================================
    # 🛡️ [مجموعة إدارة جلسات المتصفح - Browser Session Management]
    # ========================================================================

    # مسار إلغاء ثقة جلسة متصفح معينة (سحب الصلاحية)
    # يستقبل session_id رقمياً، محمي بـ POST فقط
    # الاستخدام: تسجيل الخروج من متصفح مريب أو جهاز مفقود
    path('session/<int:session_id>/revoke/', views.revoke_browser_session, name='revoke_session'),

    # مسار توثيق جلسة متصفح (جعلها موثوقة)
    # يستقبل session_id رقمياً، محمي بـ POST فقط
    # الاستخدام: وضع علامة على متصفح يستخدمه المستخدم بانتظام كموثوق
    path('session/<int:session_id>/trust/', views.mark_browser_trusted, name='trust_session'),
]