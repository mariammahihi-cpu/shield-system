from django.db import models
from django.conf import settings


class Alert(models.Model):
    ALERT_TYPES = [
        ('volume_variance',     'عجز في الحجم القياسي (ASTM)'),
        ('geofence_violation',  'تجاوز النطاق الجغرافي (GPS)'),
        ('seal_tampering',      'محاولة تلاعب بختم QR'),
        #('unauthorized_device', 'تسجيل دخول من جهاز غير مصرح'),
    ]
    SEVERITY_LEVELS = [
        ('low',      'منخفض'),
        ('medium',   'متوسط'),
        ('critical', 'حرج'),
    ]

    trip             = models.ForeignKey('trips.Trip', on_delete=models.PROTECT, related_name='trip_alerts')
    alert_type       = models.CharField(max_length=50, choices=ALERT_TYPES)
    severity         = models.CharField(max_length=20, choices=SEVERITY_LEVELS)
    description      = models.TextField(verbose_name="تفاصيل الإنذار")
    is_resolved      = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True, null=True)
    resolved_by      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_alerts')
    created_at       = models.DateTimeField(auto_now_add=True)
    resolved_at      = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"إنذار {self.get_severity_display()} - {self.trip.trip_code}"

    class Meta:
        db_table = 'shield_alerts'
        verbose_name = 'إنذار'
        verbose_name_plural = 'الإنذارات'
        ordering = ['-created_at']


class CorrectionRequest(models.Model):
    STATUS_CHOICES = [
        ('pending',  'قيد المراجعة'),
        ('approved', 'تمت الموافقة'),
        ('rejected', 'مرفوض'),
    ]

    alert        = models.ForeignKey(Alert, on_delete=models.PROTECT, related_name='correction_requests')
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='submitted_corrections')
    reason       = models.TextField(verbose_name="سبب طلب التصحيح")
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_corrections')
    review_notes = models.TextField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    reviewed_at  = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"طلب تصحيح - {self.alert} - {self.get_status_display()}"

    class Meta:
        db_table = 'shield_correction_requests'
        verbose_name = 'طلب تصحيح'
        verbose_name_plural = 'طلبات التصحيح'
        ordering = ['-created_at']