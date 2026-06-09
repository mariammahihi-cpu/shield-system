from django.db import models
from django.conf import settings

class Station(models.Model):
    customer_number = models.CharField(max_length=50, unique=True, verbose_name="رقم الزبون")
    station_name = models.CharField(max_length=255, verbose_name="اسم المحطة")
    company_branch = models.CharField(max_length=100, verbose_name="فرع الشركة")
    city = models.CharField(max_length=100, verbose_name="المدينة")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="خط العرض المرجعي")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="خط الطول المرجعي")
    is_active = models.BooleanField(default=True, verbose_name="نشطة")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stations'


class Warehouse(models.Model):
    warehouse_code = models.CharField(max_length=50, unique=True, verbose_name="رمز المستودع")
    warehouse_name = models.CharField(max_length=255, verbose_name="اسم المستودع")
    location_city = models.CharField(max_length=100, verbose_name="المدينة")
    address_details = models.TextField(verbose_name="تفاصيل العنوان")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'warehouses'


class Driver(models.Model):
    national_id = models.CharField(max_length=20, unique=True, verbose_name="الرقم الوطني")
    driver_name = models.CharField(max_length=255, verbose_name="اسم السائق")
    license_number = models.CharField(max_length=50, unique=True, verbose_name="رقم رخصة القيادة")
    phone_number = models.CharField(max_length=15, unique=True, verbose_name="رقم الهاتف")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'drivers'


class Truck(models.Model):
    STATUS_CHOICES = [
        ('active', 'في الخدمة'),
        ('maintenance', 'صيانة'),
        ('out_of_service', 'خارج الخدمة'),
    ]
    truck_id = models.CharField(max_length=50, unique=True, verbose_name="رقم الشاحنة / اللوحة")
    driver = models.ForeignKey(Driver, on_delete=models.PROTECT, verbose_name="السائق المعين")
    capacity_liters = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعة باللتر")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="حالة الشاحنة")
    last_inspection_date = models.DateField(verbose_name="تاريخ آخر فحص")
    is_gps_active = models.BooleanField(default=True, verbose_name="حالة جهاز الـ GPS")

    class Meta:
        db_table = 'shield_trucks'


class Trip(models.Model):
    STATUS_CHOICES = [
        ('created', 'تم الإنشاء'),
        ('in_transit', 'في الطريق'),
        ('arrived', 'وصلت المحطة'),
        ('completed', 'مكتملة ومفرغة'),
        ('canceled', 'ملغاة'),
    ]
    trip_code = models.CharField(max_length=100, unique=True, verbose_name="رمز الرحلة (QR)")
    dispatcher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='dispatched_trips', verbose_name="موظف المستودع")
    agent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='received_trips', verbose_name="مندوب المحطة")
    truck = models.ForeignKey(Truck, on_delete=models.PROTECT, verbose_name="الشاحنة")
    station = models.ForeignKey(Station, on_delete=models.PROTECT, verbose_name="محطة الوصول")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, verbose_name="مستودع الشحن")
    shipped_volume_15c = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="الحجم القياسي المشحون عند 15°C")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created', verbose_name="حالة الرحلة")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shield_trips'


# الجدول الجديد لحل مشكلة المطابقة الفيزيائية والتوثيق الجغرافي
class DischargeRecord(models.Model):
    trip = models.OneToOneField(Trip, on_delete=models.CASCADE, related_name='discharge_record', verbose_name="الرحلة المرتبطة")
    discharge_volume = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="الحجم الفعلي المفرغ (الظاهري)")
    discharge_temperature = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="درجة الحرارة عند التفريغ")
    discharge_density = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="الكثافة المقاسة عند التفريغ")
    standardized_discharge_volume = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="الحجم القياسي المحسوب (ASTM D1250)")
    variance_liters = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="فارق العجز باللتر")
    agent_scanned_lat = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="خط العرض الفعلي لحظة المسح")
    agent_scanned_lng = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="خط الطول الفعلي لحظة المسح")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="وقت توثيق التفريغ")

    class Meta:
        db_table = 'shield_discharge_records'

    def __str__(self):
        return f"سجل تفريغ الرحلة {self.trip.trip_code}"
