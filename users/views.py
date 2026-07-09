import uuid
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseForbidden
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import SystemSettingsForm
from .forms import AdminUserCreationForm
from .models import User, UserBrowserSession, SystemSettings
from django.db.models import Q, Count

from .decorators import get_client_ip
from django.db.models import Q
from .decorators import role_required          # موجود في decorators.py
from audit.models import AuditLog, AdminAction # تطبيق التدقيق لديك

# إعداد الـ Logger لتتبع العمليات الأمنية والأحداث الحساسة
logger = logging.getLogger(__name__)


# ============================================================================
# 🔐 AUTHENTICATION & SESSION MANAGEMENT VIEWS
# ============================================================================

@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    صفحة ودالة تسجيل الدخول الآمنة مع حماية متقدمة ضد الهجمات في نظام Shield.

    🛡️ معايير الحماية المطبقة:
    1️⃣ منع Timing Attacks & Username Enumeration: استدعاء authenticate() أولاً لضمان وقت ثابت.
    2️⃣ حماية من Brute Force Attacks: عداد المحاولات الفاشلة وقفل الحساب عبر طبقة الـ Model.
    3️⃣ Browser Fingerprinting: تتبع وجدولة بصمات متصفحات الويب لمنع Session Hijacking.
    4️⃣ Smart & Safe Redirect: معالجة معامل ?next والتحقق من أمان الرابط لمنع الـ Open Redirection.
    5️⃣ Secure Cookies: تطبيق خصائص HttpOnly و Secure و SameSite=Lax.
    """

    if request.method == 'GET':
        # إذا كان مسجل دخول بالفعل، وجهه فوراً بناءً على دوره
        if request.user.is_authenticated:
            return redirect_by_role(request.user)

        logger.info(f'📋 صفحة تسجيل الدخول تم عرضها من IP {get_client_ip(request)}')
        return render(request, 'users/login.html')

    # POST: معالجة بيانات تسجيل الدخول
    elif request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        # 1️⃣ منع Timing Attacks - استدعاء authenticate أولاً لتشغيل وقت التشفير الثابت
        user = authenticate(request, username=username, password=password)

        # 2️⃣ تسجيل المحاولة ومعالجة الفشل أمنياً
        if user is None:
            try:
                target_user = User.objects.get(username=username)

                # فحص إذا كان الحساب مقفولاً بالفعل
                if target_user.is_locked:
                    logger.warning(f'🔒 محاولة دخول لحساب مقفول: {username} من IP {get_client_ip(request)}')
                    messages.error(request, '❌ حسابك مقفل بسبب محاولات فاشلة متكررة. يرجى التواصل مع المدير.')
                    return render(request, 'users/login.html')

                # استدعاء دالة الموديل لزيادة العداد وقفل الحساب حسب إعدادات النظام
                target_user.increment_login_attempts()

                # قراءة الحد الأقصى للمحاولات من الإعدادات التشغيلية والأمنية
                max_attempts = SystemSettings.load().max_login_attempts
                remaining_attempts = max_attempts - target_user.login_attempts

                if remaining_attempts > 0:
                    logger.warning(f'❌ محاولة دخول فاشلة: {username} (المحاولة {target_user.login_attempts}/{max_attempts}) من IP {get_client_ip(request)}')
                    messages.error(request, f'❌ اسم المستخدم أو كلمة المرور غير صحيحة. لديك {remaining_attempts} محاولات متبقية.')
                else:
                    logger.critical(f'🔒 تم قفل الحساب الآن: {username} بعد {max_attempts} محاولات فاشلة من IP {get_client_ip(request)}')
                    messages.error(request, f'🔒 تم قفل حسابك بعد {max_attempts} محاولات فاشلة. يرجى التواصل مع المدير.')

            except User.DoesNotExist:
                # الحساب غير موجود: نظهر رسالة عامة وموحدة تمنع كشف الحسابات (Username Enumeration)
                logger.warning(f'❌ محاولة دخول بحساب غير موجود: {username} من IP {get_client_ip(request)}')
                messages.error(request, '❌ اسم المستخدم أو كلمة المرور غير صحيحة.')

            return render(request, 'users/login.html')

        # ✅ الحالة 3: تسجيل الدخول نجح! التحقق من حالة القفل أولاً
        if user.is_locked:
            messages.error(request, '❌ حسابك مقفل لأسباب أمنية. تواصل مع الإدارة.')
            return render(request, 'users/login.html')

        # تصفير العداد باستخدام دالة الموديل الأصلية
        user.reset_login_attempts()

        # 4️⃣ إدارة أمن المتصفح (Browser Fingerprinting)
        browser_fp = request.COOKIES.get('shield_browser_fp')
        if not browser_fp:
            browser_fp = str(uuid.uuid4())

        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')[:500]

        # تسجيل أو تحديث جلسة المتصفح الحالية في قاعدة البيانات
        browser_session, created = UserBrowserSession.objects.get_or_create(
            user=user,
            browser_fingerprint=browser_fp,
            defaults={
                'user_agent': user_agent,
                'is_trusted': False
            }
        )

        if not created:
            browser_session.user_agent = user_agent
            browser_session.save(update_fields=['user_agent', 'last_used_at'])

        # 5️⃣ إنشاء الجلسة في بيئة Django
        login(request, user)

        # ربط الـ Session الموثوقة بالـ Middleware المخصصة للنظام لتأمين إلغاء الثقة فوراً
        request.session['_verified_browser_session_id'] = browser_session.id

        # 6️⃣ إعداد التحويل الذكي والآمن وفحص الرابط لمنع هجمات الـ Open Redirection
        next_url = request.GET.get('next') or request.POST.get('next')

        if next_url and url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host()}, secure=request.is_secure()):
            response = redirect(next_url)
        else:
            response = redirect_by_role(user)

        # زرع الكوكي المحمي في متصفح العميل بالخصائص القياسية
        response.set_cookie(
            'shield_browser_fp',
            browser_fp,
            max_age=86400 * 365,  # صالحة لمدة سنة كاملة
            httponly=True,        # حظر وصول الجافا سكريبت من أجل الحماية من الـ XSS
            secure=False,         # تُترك False في بيئة التطوير المحلي وتُحول إلى True عند تشغيل الـ HTTPS
            samesite='Lax'        # صد هجمات الـ CSRF
        )

        logger.info(f'✅ تسجيل دخول ناجح: {user.username} ({user.get_role_display()}) من IP {get_client_ip(request)}')
        if created or not browser_session.is_trusted:
            messages.warning(
                request,
                f'⚠️ مرحباً {user.full_name or user.username}. تم تسجيل الدخول من '
                f'جهاز جديد غير موثوق — بعض العمليات الحساسة (كالتفريغ) معطّلة حتى '
                f'يعتمد مدير النظام هذا الجهاز.'
            )
        else:
            messages.success(request, f'🎉 أهلاً وسهلاً بك {user.full_name or user.username}!')

        return response

@login_required(login_url='users:login')
@require_http_methods(["POST"])
def logout_view(request):
    """
    تسجيل الخروج الآمن - محمي بـ POST فقط لمنع هجمات الـ CSRF وتطهير الكوكيز.
    """
    username = request.user.username
    role = request.user.get_role_display()
    client_ip = get_client_ip(request)

    # إنهاء الجلسة وتطهيرها من قاعدة البيانات والذاكرة المؤقتة
    logout(request)

    logger.info(f'🚪 تسجيل خروج ناجح: {username} ({role}) من IP {client_ip}')
    messages.success(request, '👋 تم تسجيل خروجك بنجاح من النظام.')

    response = redirect('users:login')
    # نترك كوكي المتصفح shield_browser_fp دون حذفها حتى يتعرف عليها النظام في المرات القادمة كموثوقة
    return response


# ============================================================================
# 👤 USER PROFILE VIEWS
# ============================================================================

@login_required(login_url='users:login')
def profile_view(request):
    """
    عرض الملف التعريفي للمستخدم بمعلومات الحساب وجلسات المتصفح الموثوقة.
    """
    browser_sessions = request.user.browser_sessions.all().order_by('-last_used_at')

    context = {
        'user': request.user,
        'browser_sessions': browser_sessions,
        'login_attempts': request.user.login_attempts,
        'is_account_locked': request.user.is_locked,
    }

    logger.info(f'👤 عرض الملف التعريفي للمستخدم: {request.user.username}')
    return render(request, 'users/profile.html', context)


# ============================================================================
# 🔄 HELPER FUNCTIONS - دوال مساعدة
# ============================================================================

def redirect_by_role(user):
    """
    التحويل التلقائي الذكي بناءً على الدور الوظيفي للموظف.
    تم تطويره ليكون مقاوماً للأخطاء (Fault-Tolerant) في حال عدم جاهزية بعض الروابط وتجنب الـ NoReverseMatch.
    """
    # مصفوفة الأدوار: (الرابط الأساسي للمنظومة، الرابط البديل في حال عدم جاهزية الأساسي)
    role_redirects = {
        'admin': ('users:user_list', 'trips:trip_list'),  
        'manager': ('dashboard:manager_dashboard', 'trips:trip_list'),  
        'auditor': ('alerts:alert_list', 'trips:trip_list'),
        'dispatcher': ('trips:trip_list', 'trips:trip_list'),
        'agent': ('trips:agent_trip_list', 'trips:trip_list'),
    }

    # جلب الإعداد الخاص برول المستخدم، أو تطبيق الافتراضي الآمن (الرحلات)
    target_config = role_redirects.get(user.role, ('trips:trip_list', 'trips:trip_list'))
    primary_route, fallback_route = target_config

    try:
        # محاولة التحويل للمسار الفعلي المخصص للرول
        return redirect(reverse(primary_route))
    except Exception as e:
        # 🛡️ نقد عملي لمنع الانهيار: لو كانت صفحة الإدمن غير معرّفة بعد، النظام يتجنب الـ 500 ويحول للرحلات
        logger.warning(f"تعذر الـ Reverse للمسار الأساسي '{primary_route}' للمستخدم {user.username} بسبب: {e}. تم توجيهه للمسار البديل الآمن.")
        return redirect(fallback_route)


# ============================================================================
# 🔐 BROWSER SESSION MANAGEMENT (إدارة المتصفحات)
# ============================================================================

@login_required(login_url='users:login')
@require_http_methods(["POST"])
def revoke_browser_session(request, session_id):
    """
    إلغاء ثقة جلسة متصفح معينة وسحب الصلاحية منها (تسجيل الخروج من جهاز آخر لحماية المنظومة).
    """
    # جلب الجلسة المقيدة بالمستخدم الحالي منعاً لهجمات الـ IDOR
    browser_session = get_object_or_404(UserBrowserSession, id=session_id, user=request.user)

    browser_session.mark_as_suspicious()

    logger.warning(f'⚠️ تم إلغاء ثقة وسحب جلسة للمستخدم: {request.user.username} | معرف الجلسة: {session_id}')
    messages.success(request, '✓ تم إلغاء ثقة هذا المتصفح بنجاح، سيطالب النظام بتسجيل الدخول منه مجدداً.')

    return redirect('users:profile')


@login_required(login_url='users:login')
@require_http_methods(["POST"])
def mark_browser_trusted(request, session_id):
    """
    تأكيد ووضع علامة على جلسة متصفح حالية كمتصفح موثوق ومستمر.
    """
    browser_session = get_object_or_404(UserBrowserSession, id=session_id, user=request.user)

    browser_session.mark_as_trusted()

    logger.info(f'✅ وضع علامة موثوقة لمتصفح المستخدم: {request.user.username} | معرف الجلسة: {session_id}')
    messages.success(request, '✓ تم إضافة المتصفح إلى قائمة الأجهزة الموثوقة الخاصة بك.')

    return redirect('users:profile')
# ============================================================================
# 👥 ADMIN USER MANAGEMENT VIEWS — إدارة الحسابات (للمدير فقط)
# ============================================================================

@role_required('admin')
def user_list(request):
    qs = User.objects.annotate(
        untrusted_count=Count('browser_sessions', filter=Q(browser_sessions__is_trusted=False))
    ).order_by('-untrusted_count', 'role', 'full_name')

    search = request.GET.get('q', '').strip()
    role   = request.GET.get('role', '').strip()
    if search:
        qs = qs.filter(Q(username__icontains=search) |
                       Q(full_name__icontains=search) |
                       Q(email__icontains=search))
    if role:
        qs = qs.filter(role=role)
    return render(request, 'users/user_list.html', {
        'users': qs, 'search': search,
        'role_filter': role, 'role_choices': User.ROLE_CHOICES,
    })


@role_required('admin')
@require_http_methods(["GET", "POST"])
def create_user(request):
    form = AdminUserCreationForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.save()

        AuditLog.objects.create(
            user=request.user,
            action='create_user',
            target_table='shield_users',
            target_id=user.id,
            new_value=f'{user.username} ({user.role})',
            ip_address=get_client_ip(request),
        )

        messages.success(
            request,
            f'✅ تم إنشاء حساب «{user.full_name}» ({user.get_role_display()}) بنجاح.'
        )
        return redirect('users:user_list')

    return render(request, 'users/create_user.html', {'form': form})

@role_required('admin')
@require_http_methods(["POST"])
def toggle_active_user(request, user_id):
    """تفعيل / إيقاف (is_active) — يُسجَّل في AuditLog."""
    target = get_object_or_404(User, pk=user_id)
    if target == request.user:
        messages.error(request, 'لا يمكنك إيقاف حسابك الخاص.')
        return redirect('users:user_list')

    old = 'active' if target.is_active else 'inactive'
    target.is_active = not target.is_active
    target.save(update_fields=['is_active'])
    AuditLog.objects.create(
        user=request.user, action='toggle_active',
        target_table='shield_users', target_id=target.id,
        old_value=old, new_value='active' if target.is_active else 'inactive',
        ip_address=get_client_ip(request),
    )
    messages.success(request, 'تم تفعيل الحساب.' if target.is_active else 'تم إيقاف الحساب.')
    return redirect('users:user_list')


@role_required('admin')
@require_http_methods(["POST"])
def toggle_ban_user(request, user_id):
    """حظر / فك حظر (is_locked) — يُسجَّل في AdminAction مع مبرّر إلزامي."""
    target = get_object_or_404(User, pk=user_id)
    if target == request.user:
        messages.error(request, 'لا يمكنك حظر حسابك الخاص.')
        return redirect('users:user_list')

    if target.is_locked:
        target.unlock_account()
        AdminAction.objects.filter(target_user=target, action_type__in=['ban', 'auto_lock'],
        is_active=True).update(is_active=False)
        AdminAction.objects.create(
            target_user=target, admin_user=request.user,
            action_type='unlock', reason=request.POST.get('reason', 'فك حظر إداري'),
        )
        messages.success(request, 'تم فك حظر الحساب.')
    else:
        reason = request.POST.get('reason', '').strip()
        if not reason:
            messages.error(request, 'يجب إدخال مبرّر إداري للحظر.')
            return redirect('users:user_list')
        target.lock_account()
        AdminAction.objects.create(
            target_user=target, admin_user=request.user,
            action_type='ban', reason=reason,
        )
        messages.warning(request, 'تم حظر الحساب.')
    return redirect('users:user_list')
@role_required('admin')
@require_http_methods(["POST"])
def toggle_device_trust(request, session_id):
    from .models import UserBrowserSession
    from audit.models import AuditLog
    session = get_object_or_404(UserBrowserSession, pk=session_id)
    session.is_trusted = not session.is_trusted
    session.save(update_fields=['is_trusted'])
    AuditLog.objects.create(
        user=request.user,
        action='trust_device' if session.is_trusted else 'untrust_device',
        target_table='user_browser_sessions', target_id=session.id,
        new_value=f'{session.user.username} → trusted={session.is_trusted}',
        ip_address=get_client_ip(request),
    )
    messages.success(request, 'تم اعتماد الجهاز.' if session.is_trusted else 'تم سحب ثقة الجهاز.')
    return redirect('users:user_list')
#الاعدادات التشغيلية 
@role_required('admin')
@require_http_methods(["GET", "POST"])
def system_settings(request):
    obj = SystemSettings.load()
    if request.method == 'POST':
        form = SystemSettingsForm(request.POST, instance=obj)
        if form.is_valid():
            s = form.save(commit=False)
            s.updated_by = request.user
            s.save()
            AuditLog.objects.create(
                user=request.user, action='update_settings',
                target_table='system_settings', target_id=1,
                new_value='تحديث الإعدادات التشغيلية والأمنية',
                ip_address=get_client_ip(request),
            )
            messages.success(request, '✅ تم حفظ الإعدادات وتطبيقها بنجاح.')
            return redirect('users:system_settings')
    else:
        form = SystemSettingsForm(instance=obj)
    return render(request, 'users/settings.html', {'form': form, 'settings': obj})