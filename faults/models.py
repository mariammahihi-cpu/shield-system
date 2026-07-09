from django.db import models
from django.conf import settings


class MechanicalFault(models.Model):
    FAULT_TYPES = [
        ('valve_leak',       'تسريب في الصمامات'),
        ('gps_sensor',       'عطل في نظام GPS'),
        ('meter_fault',      'خلل في عداد التدفق'),
        ('reading_variance', 'فارق في القراءات الفيزيائية'),
        ('other',            'أخرى'),
    ]
    STATUS_CHOICES = [
        ('open',    'مفتوح'),
        ('fixing',  'قيد الإصلاح'),
        ('closed',  'تمت الصيانة'),
    ]

    truck        = models.ForeignKey('trips.Truck', on_delete=models.CASCADE, null=True, blank=True, related_name='fault_reports', verbose_name="الشاحنة")
    trip         = models.ForeignKey('trips.Trip', on_delete=models.SET_NULL, null=True, blank=True, related_name='fault_reports', verbose_name="الرحلة المرتبطة")
    station      = models.ForeignKey('trips.Station', on_delete=models.SET_NULL, null=True, blank=True, related_name='fault_reports', verbose_name="المحطة المرتبطة")
    reported_by  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='reported_faults', verbose_name="مبلغ البلاغ")
    fault_type   = models.CharField(max_length=50, choices=FAULT_TYPES, verbose_name="نوع العطل")
    description  = models.TextField(verbose_name="وصف العطل")
    action_taken = models.TextField(blank=True, null=True, verbose_name="تفاصيل الإجراء المتخذ")
    photo        = models.ImageField(upload_to='fault_reports/%Y/%m/', blank=True, null=True, verbose_name="صورة العطل")
    is_critical  = models.BooleanField(default=False, verbose_name="هل يمنع التشغيل؟")
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at   = models.DateTimeField(auto_now_add=True)
    resolved_at  = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        target = self.truck.truck_id if self.truck else (self.station.station_name if self.station else 'غير محدد')
        return f"بلاغ عطل - {target} - {self.get_status_display()}"

    class Meta:
        db_table = 'shield_mechanical_faults'
        verbose_name = 'بلاغ عطل ميكانيكي'
        verbose_name_plural = 'بلاغات الأعطال الميكانيكية'
        ordering = ['-created_at']