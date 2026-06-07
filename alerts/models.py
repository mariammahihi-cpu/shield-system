from django.db import models
from django.conf import settings


class Alert(models.Model):
    ALERT_TYPES = [
        ('volume_variance',   'عجز في الحجم القياسي (ASTM)'),
        ('geofence_violation', 'تجاوز النطاق الجغرافي (GPS)'),
        ('seal_tampering',    'محاولة تلاعب بختم QR'),
        ('unauthorized_device', 'تسجيل دخول من جهاز غير مصرح'),
    ]
    SEVERITY_LEVELS = [
        ('low',      'منخفض'),
        ('medium',   'متوسط'),
        ('critical', 'حرج'),
    ]

    trip        = models.ForeignKey('trips.Trip', on_delete=models.PROTECT, related_name='trip_alerts')
    alert_type  = models.CharField(max_length=50, choices=ALERT_TYPES)
    severity    = models.CharField(max_length=20, choices=SEVERITY_LEVELS)
    description = models.TextField(verbose_name="تفاصيل الإنذار")
    is_resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True, null=True)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_alerts')
    created_at  = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"إنذار {self.get_severity_display()} - {self.trip.trip_code}"

    class Meta:
        db_table = 'shield_alerts'


class CorrectionRequest(models.Model):
    STATUS_CHOICES = [
        ('pending',  'قيد المراجعة'),
        ('approved', 'تمت الموافقة'),
        ('rejected', 'مرفوض'),
    ]

    trip             = models.ForeignKey('trips.Trip', on_delete=models.PROTECT, related_name='correction_requests')
    requester        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='submitted_requests')
    field_to_correct = models.CharField(max_length=50, verbose_name="الحقل المراد تعديله")
    old_value        = models.CharField(max_length=255, verbose_name="القيمة القديمة")
    new_value        = models.CharField(max_length=255, verbose_name="القيمة الجديدة")
    reason           = models.TextField(verbose_name="مبررات الطلب")
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewer         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_requests')
    review_notes     = models.TextField(null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    reviewed_at      = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"طلب تصحيح - {self.trip.trip_code} - {self.get_status_display()}"

    class Meta:
        db_table = 'shield_correction_requests'
