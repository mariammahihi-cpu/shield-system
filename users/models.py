from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin',      'مدير النظام'),
        ('auditor',    'المراقب'),
        ('manager',    'المدير العام'),
        ('dispatcher', 'موظف المستودع'),
        ('agent',      'مندوب المحطة'),
    ]

    full_name     = models.CharField(max_length=255, verbose_name="الاسم الكامل")
    role          = models.CharField(max_length=30, choices=ROLE_CHOICES, verbose_name="الدور")
    phone_number  = models.CharField(max_length=15, blank=True, null=True)
    login_attempts = models.PositiveIntegerField(default=0)
    is_locked     = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name} - {self.get_role_display()}"

    class Meta:
        db_table = 'shield_users'
class UserDevice(models.Model):
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='devices',
        verbose_name="المستخدم"
    )
    device_uuid  = models.CharField(max_length=255, verbose_name="البصمة الرقمية")
    device_name  = models.CharField(max_length=100, blank=True, null=True, verbose_name="اسم الجهاز")
    is_verified  = models.BooleanField(default=True, verbose_name="هل الجهاز موثق؟")
    bound_at     = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الربط")
    last_login_at = models.DateTimeField(auto_now=True, verbose_name="آخر ظهور")

    def __str__(self):
        return f"{self.user.full_name} - {self.device_name or 'غير معروف'}"

    class Meta:
        db_table = 'user_devices'
        verbose_name = 'جهاز مستخدم'
