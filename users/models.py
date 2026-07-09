from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator


# ============================================================================
# 👤 USER MODEL - نموذج المستخدم المخصص للمنظومة
# ============================================================================

class User(AbstractUser):
    """
    نموذج المستخدم المخصص لمنظومة Shield.
    
    يرث من AbstractUser ويضيف حقول مخصصة لإدارة الأدوار والأمان والتتبع.
    
    الأدوار المسموحة:
    - admin: مدير النظام (صلاحيات كاملة)
    - auditor: المراقب (قراءة فقط، عرض التقارير والشحنات المشبوهة)
    - manager: المدير العام (إدارة الرحلات والموظفين)
    - dispatcher: موظف المستودع (إرسال الرحلات)
    - agent: مندوب المحطة (استقبال وتفريغ الشحنات)
    """
    
    ROLE_CHOICES = [
        ('admin', 'مدير النظام'),
        ('auditor', 'المراقب'),
        ('manager', 'المدير العام'),
        ('dispatcher', 'موظف المستودع'),
        ('agent', 'مندوب المحطة'),
    ]
    
    full_name = models.CharField(
        max_length=255,
        verbose_name="الاسم الكامل",
        help_text="الاسم الكامل للمستخدم"
    )
    
    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default='agent',
        verbose_name="الدور الوظيفي",
        help_text="تحديد الدور الوظيفي والصلاحيات المرتبطة به"
    )

    national_id = models.CharField(
    max_length=20, unique=True, null=True, blank=True,
    verbose_name="الرقم الوطني",
    validators=[RegexValidator(regex=r'^\d{6,20}$', message='الرقم الوطني أرقام فقط (6-20 خانة).')],
    )
    
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True,
        verbose_name="رقم الهاتف",
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='رقم الهاتف يجب أن يكون من 9 إلى 15 رقماً'
            )
        ],
        help_text="رقم الهاتف للتواصل (اختياري)"
    )
    notifications_seen_at = models.DateTimeField(null=True, blank=True, verbose_name="آخر اطّلاع على الإشعارات")
    audit_seen_at = models.DateTimeField(null=True, blank=True, verbose_name="آخر اطّلاع على سجل التدقيق")
    # 🔐 حقول الأمان - لمنع الاختراق عبر محاولات الدخول المتكررة
    login_attempts = models.PositiveIntegerField(
        default=0,
        verbose_name="عدد محاولات الدخول الفاشلة",
        help_text="عداد لعدد محاولات تسجيل الدخول الفاشلة المتتالية"
    )
    
    is_locked = models.BooleanField(
        default=False,
        verbose_name="قفل الحساب",
        help_text="إذا كان True، يكون الحساب مقفولاً ولا يمكن الدخول"
    )
    
    # ضبط الحقول المطلوبة عند إنشاء مستخدم جديد عبر الـ Terminal
    REQUIRED_FIELDS = ['email', 'full_name', 'role']
    
    class Meta:
        db_table = 'shield_users'
        verbose_name = 'مستخدم'
        verbose_name_plural = 'المستخدمون'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_locked']),
        ]
    
    def __str__(self):
        """عرض اسم المستخدم مع الدور الوظيفي عند استدعائه في لوحة التحكم."""
        if self.full_name:
            return f"{self.full_name} ({self.get_role_display()})"
        return f"{self.username} ({self.get_role_display()})"
    
    def lock_account(self):
        """قفل الحساب بسبب محاولات دخول فاشلة متكررة."""
        self.is_locked = True
        self.save(update_fields=['is_locked', 'login_attempts'])

    # تسجيل سبب مقروء للقفل التلقائي (يُعرض للمدير عند المراجعة)
        from audit.models import AdminAction
        AdminAction.objects.create(
        target_user=self, admin_user=None, action_type='auto_lock',
        reason=f'قفل تلقائي بعد تجاوز الحد الأقصى لمحاولات الدخول الفاشلة ({self.login_attempts} محاولات).',
    )
    
    def unlock_account(self):
        """فتح قفل الحساب وإعادة تعيين عداد المحاولات الفاشلة كلياً."""
        self.is_locked = False
        self.login_attempts = 0
        self.save(update_fields=['is_locked', 'login_attempts'])
    #تم تعديل عدد المحاولات ل 3
    def increment_login_attempts(self):
        """زيادة عداد محاولات الدخول الفاشلة وتفعيل القفل التلقائي حسب إعدادات النظام."""
        self.login_attempts += 1
        max_attempts = SystemSettings.load().max_login_attempts
        if self.login_attempts >= max_attempts:
           self.lock_account()
        else:
           self.save(update_fields=['login_attempts'])

    def reset_login_attempts(self):
        """إعادة تعيين عداد المحاولات عند نجاح المستخدم في الدخول لتصفير العداد."""
        if self.login_attempts > 0:
            self.login_attempts = 0
            self.save(update_fields=['login_attempts'])


# ============================================================================
# 🌐 USER BROWSER SESSION MODEL - تتبع جلسات المتصفحات (Web-Only)
# ============================================================================

class UserBrowserSession(models.Model):
    """
    نموذج تتبع جلسات المتصفحات المعتمدة - بديل هندسي متوافق مع بيئة الويب.
    
    الآلية الأمنية:
    1. عند الدخول، نولد بصمة متصفح فريدة (browser_fingerprint).
    2. نرسل المعرّف في Cookie آمن من نوع (HttpOnly + Secure) لمنع سرقته برمجياً.
    3. الـ Views تقارن البصمة القادمة من الكوكي مع المسجل هنا لحظر الـ Session Hijacking.
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='browser_sessions',
        verbose_name="المستخدم"
    )
    
    browser_fingerprint = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="بصمة المتصفح",
        help_text="معرّف فريد للمتصفح يتم توليده وتخزينه في Secure/HttpOnly Cookie"
    )
    
    user_agent = models.CharField(
        max_length=500,
        verbose_name="معلومات المتصفح",
        help_text="نوع ونسخة المتصفح ونظام التشغيل (User-Agent Header)"
    )
    
    is_trusted = models.BooleanField(
        default=True,
        verbose_name="متصفح موثق",
        help_text="هل تم التحقق من هذا المتصفح وتم اعتباره آمناً"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ أول جلسة"
    )
    
    last_used_at = models.DateTimeField(
        auto_now=True,
        verbose_name="تاريخ آخر استخدام"
    )
    
    class Meta:
        db_table = 'user_browser_sessions'
        verbose_name = 'جلسة متصفح'
        verbose_name_plural = 'جلسات المتصفحات'
        ordering = ['-last_used_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'browser_fingerprint'],
                name='unique_user_browser_fingerprint',
                violation_error_message='هذه البصمة مسجلة بالفعل لهذا المستخدم'
            )
        ]
        indexes = [
            models.Index(fields=['user', 'is_trusted']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.user_agent[:50]}"
    
    def mark_as_trusted(self):
        """وضع علامة على المتصفح كموثق وآمن."""
        self.is_trusted = True
        self.save(update_fields=['is_trusted'])
    
    def mark_as_suspicious(self):
        """وضع علامة على المتصفح كمريب وغير موثق لتنبيه المراقبين."""
        self.is_trusted = False
        self.save(update_fields=['is_trusted'])
# users/models.py — داخل UserBrowserSession
#is_primary = models.BooleanField(default=False, verbose_name="الجهاز الميداني الأساسي")


# ============================================================================
# ⚠️ تنبيهات مطابقة التكامل المعماري (مراجعة الأنظمة الأخرى)
# ============================================================================

"""
🚨 تذكير هندسي للمطورين للتأكد من مطابقة التطبيقات الأخرى:

1. في تطبيق الرحلات (trips/models.py) داخل موديل المستودع Warehouse:
   employees = models.ManyToManyField(
       settings.AUTH_USER_MODEL,
       blank=True,
       related_name='assigned_warehouses',  ← 🔑 حرج جداً لعمل الـ views
       verbose_name="الموظفون المعينون"
   )

2. في تطبيق الرحلات (trips/models.py) داخل موديل المحطة Station:
   agents = models.ManyToManyField(
       settings.AUTH_USER_MODEL,
       blank=True,
       related_name='assigned_stations',    ← 🔑 حرج جداً لعمل الـ views
       verbose_name="المندوبون المعينون"
   )

3. في ملف الإعدادات الرئيسي (settings.py):
   AUTH_USER_MODEL = 'users.User'            ← ربط النموذج المخصص بنواة دجانجو
"""
#الاعدادات التشغيلية لمدير النظام 
class SystemSettings(models.Model):
    """إعدادات تشغيلية وأمنية عامة — سجل واحد فقط (Singleton)."""
    password_validity_days   = models.PositiveIntegerField(default=90, verbose_name="مدة صلاحية كلمة المرور (يوم)")
    max_login_attempts       = models.PositiveIntegerField(default=3,  verbose_name="محاولات الدخول قبل القفل")
    default_geofence_radius  = models.PositiveIntegerField(default=50, verbose_name="نطاق الأمان الافتراضي (متر)")
    variance_alert_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=0.5, verbose_name="حد إنذار العجز (%)")
    enable_alerts            = models.BooleanField(default=True, verbose_name="تفعيل التنبيهات")
    updated_at               = models.DateTimeField(auto_now=True)
    updated_by               = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = 'system_settings'
        verbose_name = verbose_name_plural = 'إعدادات النظام'

    def save(self, *args, **kwargs):
        self.pk = 1                    # 🔑 يفرض سجلاً واحداً دائماً
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj