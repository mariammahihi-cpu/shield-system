import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone


def generate_trip_code():
    return f"SHIELD-{uuid.uuid4().hex[:8].upper()}"


def generate_qr_token():
    return uuid.uuid4()


class Station(models.Model):
    customer_number  = models.CharField(max_length=50, unique=True, verbose_name="رقم الزبون")
    station_name     = models.CharField(max_length=255, verbose_name="اسم المحطة")
    company_branch   = models.CharField(max_length=100, verbose_name="فرع الشركة")
    city             = models.CharField(max_length=100, verbose_name="المدينة")
    latitude         = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="خط العرض")
    longitude        = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="خط الطول")
    geofence_radius  = models.PositiveIntegerField(default=50, verbose_name="نطاق الأمان (متر)")
    is_active        = models.BooleanField(default=True, verbose_name="نشطة")
    is_banned        = models.BooleanField(default=False, verbose_name="موقوفة")
    agents           = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='assigned_stations', verbose_name="المندوبون المعينون")
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stations'
        verbose_name = 'محطة'
        verbose_name_plural = 'المحطات'

    def __str__(self):
        return f"{self.customer_number} - {self.station_name}"


class Warehouse(models.Model):
    warehouse_code   = models.CharField(max_length=50, unique=True, verbose_name="رمز المستودع")
    warehouse_name   = models.CharField(max_length=255, verbose_name="اسم المستودع")
    location_city    = models.CharField(max_length=100, verbose_name="المدينة")
    address_details  = models.TextField(blank=True, null=True, verbose_name="تفاصيل العنوان")
    is_active        = models.BooleanField(default=True, verbose_name="نشط")
    employees        = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='assigned_warehouses', verbose_name="الموظفون المعينون")
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'warehouses'
        verbose_name = 'مستودع'
        verbose_name_plural = 'المستودعات'

    def __str__(self):
        return f"{self.warehouse_code} - {self.warehouse_name}"


class Driver(models.Model):
    national_id     = models.CharField(max_length=20, unique=True, verbose_name="الرقم الوطني")
    driver_name     = models.CharField(max_length=255, verbose_name="اسم السائق")
    license_number  = models.CharField(max_length=50, unique=True, verbose_name="رقم رخصة القيادة")
    phone_number    = models.CharField(max_length=15, unique=True, verbose_name="رقم الهاتف")
    is_active       = models.BooleanField(default=True, verbose_name="نشط")
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'drivers'
        verbose_name = 'سائق'
        verbose_name_plural = 'السائقين'

    def __str__(self):
        return self.driver_name


class Truck(models.Model):
    STATUS_CHOICES = [
        ('active',         'في الخدمة'),
        ('maintenance',    'صيانة'),
        ('out_of_service', 'خارج الخدمة'),
    ]
    truck_id             = models.CharField(max_length=50, unique=True, verbose_name="رقم اللوحة")
    driver               = models.ForeignKey(Driver, on_delete=models.PROTECT, verbose_name="السائق المعين")
    capacity_liters      = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعة (لتر)")
    status               = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="الحالة")
    last_inspection_date = models.DateField(verbose_name="تاريخ آخر فحص")
    is_gps_active        = models.BooleanField(default=True, verbose_name="GPS مفعل")

    class Meta:
        db_table = 'shield_trucks'
        verbose_name = 'شاحنة'
        verbose_name_plural = 'الشاحنات'

    def __str__(self):
        return f"{self.truck_id} ({self.driver.driver_name})"


class Trip(models.Model):
    STATUS_CHOICES = [
        ('created',    'تم الإنشاء'),
        ('in_transit', 'في الطريق'),
        ('arrived',    'وصلت المحطة'),
        ('completed',  'مكتملة'),
        ('canceled',   'ملغاة'),
    ]

    trip_code    = models.CharField(max_length=100, unique=True, blank=True, verbose_name="رمز الرحلة")
    dispatcher   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='dispatched_trips', verbose_name="موظف المستودع")
    agent        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='received_trips', verbose_name="مندوب المحطة")
    truck        = models.ForeignKey(Truck, on_delete=models.PROTECT, verbose_name="الشاحنة")
    station      = models.ForeignKey(Station, on_delete=models.PROTECT, verbose_name="المحطة")
    warehouse    = models.ForeignKey(Warehouse, on_delete=models.PROTECT, verbose_name="المستودع")
    fuel_type    = models.CharField(max_length=10, default='petrol', editable=False, verbose_name="نوع الوقود (بنزين فقط)")
    seal_numbers = models.CharField(max_length=255, verbose_name="أرقام الأختام")

    shipped_volume_ambient = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="الحجم الظاهري المشحون (لتر)")
    shipped_temperature    = models.DecimalField(max_digits=5,  decimal_places=2, verbose_name="درجة الحرارة عند الشحن (°C)")
    shipped_density        = models.DecimalField(max_digits=6,  decimal_places=4, verbose_name="الكثافة عند الشحن")
    shipped_volume_15c     = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="الحجم القياسي عند 15°C")

    qr_token      = models.UUIDField(default=generate_qr_token, unique=True, verbose_name="توكن QR")
    qr_expires_at = models.DateTimeField(null=True, blank=True, verbose_name="انتهاء صلاحية QR")

    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created', verbose_name="الحالة")
    notes      = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shield_trips'
        verbose_name = 'رحلة'
        verbose_name_plural = 'الرحلات'
        ordering = ['-created_at']

    def __str__(self):
        return f"رحلة {self.trip_code} → {self.station.station_name} (بنزين)"

    def save(self, *args, **kwargs):
        self.fuel_type = 'petrol'
        if not self.trip_code:
            self.trip_code = generate_trip_code()
        if not self.qr_expires_at:
            self.qr_expires_at = timezone.now() + timezone.timedelta(hours=48)
        thermal_coefficient = Decimal('0.0009')
        temp_diff = self.shipped_temperature - Decimal('15')
        correction = Decimal('1') - (temp_diff * thermal_coefficient)
        self.shipped_volume_15c = self.shipped_volume_ambient * correction
        super().save(*args, **kwargs)

    def is_qr_valid(self):
        return self.qr_expires_at and timezone.now() < self.qr_expires_at

    def get_qr_status(self):
        if self.status in ('completed', 'canceled'):
            return 'closed'
        if not self.is_qr_valid():
            return 'expired'
        return 'valid'


class DischargeRecord(models.Model):
    GEOFENCE_STATUS = [
        ('green',  'داخل النطاق الآمن (0-50م)'),
        ('yellow', 'نطاق تحذير (51-150م)'),
        ('red',    'خارج النطاق (أكثر من 150م)'),
    ]

    trip              = models.OneToOneField(Trip, on_delete=models.CASCADE, related_name='discharge_record', verbose_name="الرحلة")
    agent             = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='discharge_records', verbose_name="مندوب المحطة")

    discharge_volume_ambient = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="الحجم الظاهري المفرغ (لتر)")
    discharge_temperature    = models.DecimalField(max_digits=5,  decimal_places=2, verbose_name="درجة الحرارة عند التفريغ (°C)")
    discharge_density        = models.DecimalField(max_digits=6,  decimal_places=4, verbose_name="الكثافة عند التفريغ")
    discharge_volume_15c     = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="الحجم القياسي عند 15°C")

    variance_liters  = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="فارق العجز (لتر)")
    variance_percent = models.DecimalField(max_digits=6,  decimal_places=3, default=0, verbose_name="نسبة العجز (%)")
    is_suspect       = models.BooleanField(default=False, verbose_name="شحنة مشبوهة")

    seal_check_passed = models.BooleanField(default=False, verbose_name="الأختام مطابقة؟")
    seal_notes        = models.TextField(blank=True, null=True, verbose_name="ملاحظات الأختام")

    scan_latitude    = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="خط العرض عند المسح")
    scan_longitude   = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="خط الطول عند المسح")
    scan_distance_m  = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name="المسافة عن المحطة (متر)")
    geofence_status  = models.CharField(max_length=10, choices=GEOFENCE_STATUS, default='red', verbose_name="حالة النطاق الجغرافي")

    notes      = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="وقت التفريغ")

    class Meta:
        db_table = 'shield_discharge_records'
        verbose_name = 'سجل تفريغ'
        verbose_name_plural = 'سجلات التفريغ'

    def __str__(self):
        return f"تفريغ رحلة {self.trip.trip_code}"

    def save(self, *args, **kwargs):
        thermal_coefficient = Decimal('0.0009')
        temp_diff = self.discharge_temperature - Decimal('15')
        correction = Decimal('1') - (temp_diff * thermal_coefficient)
        self.discharge_volume_15c = self.discharge_volume_ambient * correction

        shipped = self.trip.shipped_volume_15c
        self.variance_liters = shipped - self.discharge_volume_15c
        self.variance_percent = (self.variance_liters / shipped * 100) if shipped else Decimal('0')

        max_allowed = shipped * Decimal('0.005')
        self.is_suspect = self.variance_liters > max_allowed or self.variance_liters < Decimal('0')

        super().save(*args, **kwargs)