from django.db import models
from django.conf import settings


class Station(models.Model):
    customer_number = models.CharField(max_length=50, unique=True, verbose_name="رقم الزبون")
    station_name    = models.CharField(max_length=255, verbose_name="اسم المحطة")
    company_branch  = models.CharField(max_length=100, verbose_name="الشركة التابعة")
    city            = models.CharField(max_length=100, verbose_name="المدينة")
    latitude        = models.DecimalField(max_digits=10, decimal_places=8, verbose_name="خط العرض")
    longitude       = models.DecimalField(max_digits=11, decimal_places=8, verbose_name="خط الطول")
    is_active       = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer_number} - {self.station_name}"

    class Meta:
        db_table = 'stations'


class Warehouse(models.Model):
    warehouse_code  = models.CharField(max_length=30, unique=True, verbose_name="كود المستودع")
    warehouse_name  = models.CharField(max_length=255, verbose_name="اسم المستودع")
    location_city   = models.CharField(max_length=100, verbose_name="المدينة")
    address_details = models.TextField(blank=True, null=True)
    is_active       = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.warehouse_code} - {self.warehouse_name}"

    class Meta:
        db_table = 'warehouses'


class Driver(models.Model):
    national_id    = models.CharField(max_length=20, unique=True, verbose_name="الرقم الوطني")
    driver_name    = models.CharField(max_length=255, verbose_name="اسم السائق")
    license_number = models.CharField(max_length=50, unique=True, verbose_name="رخصة القيادة")
    phone_number   = models.CharField(max_length=15, unique=True, verbose_name="رقم الهاتف")
    is_active      = models.BooleanField(default=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.driver_name} ({self.license_number})"

    class Meta:
        db_table = 'drivers'


class Truck(models.Model):
    STATUS_CHOICES = [
        ('active',       'نشطة جاهزة للعمل'),
        ('maintenance',  'تحت الصيانة'),
        ('out_of_service', 'خارج الخدمة'),
    ]
    truck_id            = models.CharField(max_length=50, unique=True, verbose_name="رقم اللوحة")
    driver              = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)
    capacity_liters     = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعة (لتر)")
    status              = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    last_inspection_date = models.DateField(verbose_name="تاريخ آخر فحص")
    is_gps_active       = models.BooleanField(default=True, verbose_name="GPS مفعل؟")

    def __str__(self):
        return f"شاحنة: {self.truck_id}"

    class Meta:
        db_table = 'shield_trucks'


class Trip(models.Model):
    STATUS_CHOICES = [
        ('created',   'تم الإنشاء'),
        ('in_transit', 'في الطريق'),
        ('arrived',   'وصلت المحطة'),
        ('completed', 'مكتملة'),
        ('canceled',  'ملغاة'),
    ]
    trip_code         = models.CharField(max_length=100, unique=True, verbose_name="رمز الرحلة")
    dispatcher        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='dispatched_trips')
    agent             = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='assigned_trips')
    truck             = models.ForeignKey(Truck, on_delete=models.PROTECT)
    station           = models.ForeignKey(Station, on_delete=models.PROTECT)
    warehouse         = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    shipped_volume_15c = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="الحجم القياسي المشحون")
    status            = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"رحلة: {self.trip_code} | {self.get_status_display()}"

class Meta:
        db_table = 'shield_trips'
