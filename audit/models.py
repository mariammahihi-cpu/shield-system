from django.db import models
from django.conf import settings


class AdminAction(models.Model):
    ACTION_CHOICES = [
        ('ban',          'حظر نهائي'),
        ('suspend',      'تجميد مؤقت'),
        ('unlock',       'إلغاء قفل الحساب'),
        ('reset_device', 'إعادة تعيين جهاز معتمد'),
    ]

    target_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bans_received')
    admin_user  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='actions_taken')
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    reason      = models.TextField(verbose_name="المبرر الإداري")
    is_active   = models.BooleanField(default=True, verbose_name="هل الإجراء سارٍ؟")
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_action_type_display()} - {self.target_user.full_name}"

    class Meta:
        db_table = 'shield_admin_actions'
        verbose_name = 'إجراء إداري'


class AuditLog(models.Model):
    user         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action       = models.CharField(max_length=100, verbose_name="نوع الإجراء")
    target_table = models.CharField(max_length=100, verbose_name="الجدول المستهدف")
    target_id    = models.IntegerField(null=True, blank=True)
    ip_address   = models.CharField(max_length=50, blank=True, null=True)
    old_value    = models.TextField(blank=True, null=True)
    new_value    = models.TextField(blank=True, null=True)
    timestamp    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} - {self.target_table} - {self.timestamp}"

    class Meta:
        db_table = 'shield_audit_logs'
        verbose_name = 'سجل تدقيق'