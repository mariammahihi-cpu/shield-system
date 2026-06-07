from django.db import models
from django.conf import settings


class MechanicalFault(models.Model):
    FAULT_TYPES = [
        ('valve_leak',  'تسريب في الصمامات'),
        ('gps_sensor',  'عطل في نظام GPS'),
        ('meter_fault', 'خلل في عداد التدفق'),
        ('other',       'أخرى'),
    ]
    STATUS_CHOICES = [
        ('open',    'مفتوح'),
        ('fixing',  'قيد الإصلاح'),
        ('closed',  'تمت الصيانة'),
    ]

    truck       = models.ForeignKey('trips.Truck', on_delete=models.CASCADE, verbose_name="الشاحنة")
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name="مبلغ البلاغ")
    fault_type  = models.CharField(max_length=50, choices=FAULT_TYPES, verbose_name="نوع العطل")
    description = models.TextField(verbose_name="وصف العطل")
    is_critical = models.BooleanField(default=False, verbose_name="هل يمنع التشغيل؟")
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at  = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"بلاغ عطل - {self.truck.truck_id} - {self.get_status_display()}"

    class Meta:
        db_table = 'shield_mechanical_faults'
        verbose_name = 'بلاغ عطل ميكانيكي'
