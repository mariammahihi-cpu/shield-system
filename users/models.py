from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings # 🛠️ استيراد الإعدادات لربط المستخدم بشكل قياسي

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin',      'مدير النظام'),
        ('auditor',    'المراقب'),
        ('manager',    'المدير العام'),
        ('dispatcher', 'موظف المستودع'),
        ('agent',      'مندوب المحطة'),
    ]

    full_name      = models.CharField(max_length=255, verbose_name="الاسم الكامل")
    role           = models.CharField(max_length=30, choices=ROLE_CHOICES, verbose_name="الدور")
    phone_number   = models.CharField(max_length=15, unique=True, blank=True, null=True, verbose_name="رقم الهاتف")
    
    login_attempts = models.PositiveIntegerField(default=0, verbose_name="محاولات الدخول الفاشلة")
    is_locked      = models.BooleanField(default=False, verbose_name="هل الحساب مقفل؟")

    warehouse = models.ForeignKey(
        'trips.Warehouse', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='employees',
        verbose_name="المستودع التابع له (خاص بموظفي المستودعات)"
    )
    station = models.ForeignKey(
        'trips.Station', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='agents',
        verbose_name="المحطة التابع لها (خاص بمندوبي المحطات)"
    )

    REQUIRED_FIELDS = ['email', 'full_name', 'role']

    def __str__(self):
        display_name = self.full_name.strip() if self.full_name else self.username
        return f"{display_name} - {self.get_role_display()}"

    class Meta:
        db_table = 'shield_users'
        verbose_name = 'مستخدم'
        verbose_name_plural = 'المستخدمين'


class UserDevice(models.Model):
    # 🛠️ التعديل: استخدام settings.AUTH_USER_MODEL بدل السلسلة النصية المباشرة
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='devices',
        verbose_name="المستخدم"
    )
    
    device_uuid   = models.CharField(max_length=255, db_index=True, verbose_name="البصمة الرقمية للجهاز")
    device_name   = models.CharField(max_length=100, blank=True, null=True, verbose_name="اسم الجهاز")
    is_verified   = models.BooleanField(default=True, verbose_name="هل الجهاز موثق؟")
    bound_at      = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الربط")
    last_login_at = models.DateTimeField(auto_now=True, verbose_name="آخر ظهور")

    def __str__(self):
        display_name = self.user.full_name.strip() if self.user.full_name else self.user.username
        return f"{display_name} - {self.device_name or 'غير معروف'}"

    class Meta:
        db_table = 'user_devices'
        verbose_name = 'جهاز مستخدم'
        verbose_name_plural = 'أجهزة المستخدمين'