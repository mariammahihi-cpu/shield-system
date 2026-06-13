from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

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

    # ربط الإنذار بالرحلة
    trip        = models.ForeignKey('trips.Trip', on_delete=models.PROTECT, related_name='trip_alerts')
    alert_type  = models.CharField(max_length=50, choices=ALERT_TYPES)
    severity    = models.CharField(max_length=20, choices=SEVERITY_LEVELS)
    description = models.TextField(verbose_name="تفاصيل الإنذار")
    is_resolved = models.BooleanField(default=False, verbose_name="تمت معالجة الإنذار")
    resolution_notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات الحل")
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_alerts', verbose_name="المسؤول المعالج")
    created_at  = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"إنذار {self.get_severity_display()} - {self.trip.trip_code}"

    class Meta:
        db_table = 'shield_alerts'
        verbose_name = 'إنذار أمني'
        verbose_name_plural = 'الإنذارات الأمنية'

    def save(self, *args, **kwargs):
        # توثيق وقت حل الإنذار تلقائياً إذا تغيرت حالته إلى "تمت المعالجة"
        if self.is_resolved and not self.resolved_at:
            self.resolved_at = timezone.now()
        super().save(*args, **kwargs)


class CorrectionRequest(models.Model):
    STATUS_CHOICES = [
        ('pending',  'قيد المراجعة'),
        ('approved', 'تمت الموافقة'),
        ('rejected', 'مرفوض'),
    ]

    trip             = models.ForeignKey('trips.Trip', on_delete=models.PROTECT, related_name='correction_requests')
    requester        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='submitted_requests', verbose_name="مقدم الطلب")
    field_to_correct = models.CharField(max_length=50, verbose_name="الحقل المراد تعديله")
    old_value        = models.CharField(max_length=255, verbose_name="القيمة القديمة")
    new_value        = models.CharField(max_length=255, verbose_name="القيمة الجديدة")
    reason           = models.TextField(verbose_name="مبررات الطلب")
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="حالة الطلب")
    reviewer         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_requests', verbose_name="المراجع الإداري")
    review_notes     = models.TextField(null=True, blank=True, verbose_name="ملاحظات المراجعة")
    created_at       = models.DateTimeField(auto_now_add=True)
    reviewed_at      = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"طلب تصحيح - {self.trip.trip_code} - {self.get_status_display()}"

    class Meta:
        db_table = 'shield_correction_requests'
        verbose_name = 'طلب تصحيح بيانات'
        verbose_name_plural = 'طلبات تصحيح البيانات'

    def save(self, *args, **kwargs):
        # أتمتة ذكية: إذا وافق المدير على الطلب، يتم تعديل القيمة في الجداول الأصلية تلقائياً
        if self.pk:
            old_instance = CorrectionRequest.objects.get(pk=self.pk)
            if old_instance.status == 'pending' and self.status == 'approved':
                self.reviewed_at = timezone.now()
                
                # تنفيذ التعديل الديناميكي على جدول الرحلة أو سجل التفريغ
                target_trip = self.trip
                if hasattr(target_trip, self.field_to_correct):
                    setattr(target_trip, self.field_to_correct, self.new_value)
                    target_trip.save()
                elif hasattr(target_trip, 'discharge_record') and hasattr(target_trip.discharge_record, self.field_to_correct):
                    record = target_trip.discharge_record
                    setattr(record, self.field_to_correct, self.new_value)
                    record.save()

                # إغلاق الإنذار المرتبط تلقائياً لأن البيانات تم تصحيحها بشكل قانوني
                Alert.objects.filter(trip=self.trip, alert_type='volume_variance', is_resolved=False).update(
                    is_resolved=True,
                    resolution_notes=f"أغلق تلقائياً بناءً على طلب التصحيح المعتمد رقم {self.id}",
                    resolved_at=timezone.now()
                )
                
            elif old_instance.status == 'pending' and self.status == 'rejected':
                self.reviewed_at = timezone.now()

        super().save(*args, **kwargs)


# =====================================================================
# 🔥 الـ Signals: نظام إطلاق الإنذارات التلقائي بمجرد حدوث تلاعب
# =====================================================================

@receiver(post_save, sender='trips.DischargeRecord')
def auto_generate_variance_alert(sender, instance, created, **kwargs):
    """
    مستشعر أمني: بمجرد حفظ سجل تفريغ جديد أو تعديله، إذا ثبت وجود
    شبهة تهريب (is_suspect=True)، يتم توليد إنذار حرج فوراً في جدول الإنذارات.
    """
    if instance.is_suspect:
        # منع تكرار نفس الإنذار لنفس الرحلة
        Alert.objects.get_or_create(
            trip=instance.trip,
            alert_type='volume_variance',
            defaults={
                'severity': 'critical',
                'description': (
                    f"خطر: رصد عجز غير مسموح به في الكمية القياسية. "
                    f"الكمية المفقودة: {instance.variance_liters} لتر، "
                    f"المحطة: {instance.trip.station.station_name}."
                )
            }
        )