import qrcode
import uuid
from io import BytesIO
from decimal import Decimal
from django.core.files import File
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
        verbose_name = 'محطة'
        verbose_name_plural = 'المحطات'

    def __str__(self):
        return self.station_name


class Warehouse(models.Model):
    warehouse_code = models.CharField(max_length=50, unique=True, verbose_name="رمز المستودع")
    warehouse_name = models.CharField(max_length=255, verbose_name="اسم المستودع")
    location_city = models.CharField(max_length=100, verbose_name="المدينة")
    address_details = models.TextField(verbose_name="تفاصيل العنوان")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'warehouses'
        verbose_name = 'مستودع'
        verbose_name_plural = 'المستودعات'

    def __str__(self):
        return self.warehouse_name


class Driver(models.Model):
    national_id = models.CharField(max_length=20, unique=True, verbose_name="الرقم الوطني")
    driver_name = models.CharField(max_length=255, verbose_name="اسم السائق")
    license_number = models.CharField(max_length=50, unique=True, verbose_name="رقم رخصة القيادة")
    phone_number = models.CharField(max_length=15, unique=True, verbose_name="رقم الهاتف")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'drivers'
        verbose_name = 'سائق'
        verbose_name_plural = 'السائقين'

    def __str__(self):
        return self.driver_name


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
        verbose_name = 'شاحنة'
        verbose_name_plural = 'الشاحنات'

    def __str__(self):
        return f"{self.truck_id} ({self.driver.driver_name})"


class Trip(models.Model):
    STATUS_CHOICES = [
        ('created', 'تم الإنشاء'),
        ('in_transit', 'في الطريق'),
        ('arrived', 'وصلت المحطة'),
        ('completed', 'مكتملة ومفرغة'),
        ('canceled', 'ملغاة'),
    ]
    
    trip_code = models.CharField(max_length=100, unique=True, blank=True, verbose_name="رمز الرحلة الفريد")
    
    dispatcher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='dispatched_trips', verbose_name="موظف المستودع")
    agent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='received_trips', verbose_name="مندوب المحطة")
    truck = models.ForeignKey(Truck, on_delete=models.PROTECT, verbose_name="الشاحنة")
    station = models.ForeignKey(Station, on_delete=models.PROTECT, verbose_name="محطة الوصول")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, verbose_name="مستودع الشحن")
    
    seal_numbers = models.CharField(max_length=255, help_text="أدخل الأرقام مفصولة بفاصلة، مثال: 5501,5502,5503", verbose_name="أرقام أختام الحجرات")
    
    # بيانات الشحن (المغادرة)
    shipped_volume_ambient = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="الحجم الفعلي المشحون (الظاهري)")
    shipped_temperature    = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name="درجة الحرارة عند الشحن (°C)")
    shipped_density        = models.DecimalField(max_digits=6, decimal_places=2, default=0.00, verbose_name="الكثافة المرصودة عند الشحن")
    shipped_volume_15c     = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="الحجم القياسي المشحون عند 15°C")
    
    qr_image = models.ImageField(upload_to='qr_codes/', blank=True, null=True, verbose_name="صورة رمز QR")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created', verbose_name="حالة الرحلة")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shield_trips'
        verbose_name = 'رحلة'
        verbose_name_plural = 'الرحلات'

    def __str__(self):
        return f"رحلة {self.trip_code or self.id} -> {self.station.station_name}"

    def save(self, *args, **kwargs):
        # 1. توليد رمز الرحلة الفريد تلقائياً عند الإنشاء
        if not self.trip_code:
            self.trip_code = f"SHIELD-{uuid.uuid4().hex[:8].upper()}"

        # 2. الحساب التلقائي للحجم القياسي عند الشحن (معامل تصحيح مبسط يعتمد على درجة الحرارة القياسية 15)
        if self.shipped_volume_ambient and self.shipped_temperature:
            # معامل التمدد الحراري التقريبي للمنتجات النفطية هو 0.0009 لكل درجة مئوية
            thermal_coefficient = Decimal('0.0009')
            temp_difference = self.shipped_temperature - Decimal('15')
            correction_factor = Decimal('1') - (temp_difference * thermal_coefficient)
            self.shipped_volume_15c = self.shipped_volume_ambient * correction_factor

        generate_qr = False

        # 3. التحقق من التغييرات لتحديث الـ QR كود
        if not self.pk:
            generate_qr = True
        else:
            old_instance = Trip.objects.get(pk=self.pk)
            if (
                old_instance.truck_id != self.truck_id or
                old_instance.seal_numbers != self.seal_numbers or
                old_instance.shipped_volume_ambient != self.shipped_volume_ambient or
                old_instance.shipped_temperature != self.shipped_temperature or
                not self.qr_image
            ):
                generate_qr = True

        # 4. حفظ البيانات النصية أولاً لضمان وجود المعرفات
        super().save(*args, **kwargs)

        # 5. توليد الـ QR كود في حال وجود تعديل حساس
        if generate_qr:
            qr_content = (
                f"CODE:{self.trip_code}\n"
                f"TRUCK:{self.truck.truck_id}\n"
                f"SEALS:{self.seal_numbers}\n"
                f"VOL:{self.shipped_volume_ambient}\n"
                f"TEMP:{self.shipped_temperature}"
            )
            qr = qrcode.QRCode(version=1, box_size=6, border=4)
            qr.add_data(qr_content)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            
            filename = f"qr_{self.trip_code}.png"
            
            if self.qr_image and self.qr_image.storage.exists(self.qr_image.name):
                self.qr_image.storage.delete(self.qr_image.name)
            
            self.qr_image.save(filename, File(buffer), save=False)
            super().save(update_fields=['qr_image'])


class DischargeRecord(models.Model):
    trip = models.OneToOneField(Trip, on_delete=models.CASCADE, related_name='discharge_record', verbose_name="الرحلة المرتبطة")
    
    discharge_volume_ambient = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="الحجم الفعلي المفرغ (الظاهري)")
    discharge_temperature    = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="درجة الحرارة عند التفريغ")
    discharge_density        = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="الكثافة المقاسة عند التفريغ")
    
    # حقول يتم حسابها برمجياً وتلقائياً لحماية النظام من التلاعب اليدوي
    discharge_volume_15c     = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="الحجم القياسي المفرغ عند 15°C")
    variance_liters          = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="فارق العجز باللتر")
    is_suspect               = models.BooleanField(default=False, verbose_name="شحنة مشبوهة / احتمال تهريب")
    
    agent_scanned_lat = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="خط العرض الفعلي لحظة المسح")
    agent_scanned_lng = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="خط الطول الفعلي لحظة المسح")
    created_at        = models.DateTimeField(auto_now_add=True, verbose_name="وقت توثيق التفريغ")

    class Meta:
        db_table = 'shield_discharge_records'
        verbose_name = 'سجل تفريغ'
        verbose_name_plural = 'سجلات التفريغ'

    def __str__(self):
        return f"سجل تفريغ الرحلة {self.trip.trip_code}"

    def save(self, *args, **kwargs):
        # 1. الحساب التلقائي للحجم القياسي المفرغ عند 15 درجة مئوية
        thermal_coefficient = Decimal('0.0009')
        temp_difference = self.discharge_temperature - Decimal('15')
        correction_factor = Decimal('1') - (temp_difference * thermal_coefficient)
        self.discharge_volume_15c = self.discharge_volume_ambient * correction_factor

        # 2. حساب العجز الفعلي بناءً على مقارنة الحجوم القياسية المتناظرة (المشحون المعياري ضد المفرغ المعياري)
        if self.trip.shipped_volume_15c:
            self.variance_liters = self.trip.shipped_volume_15c - self.discharge_volume_15c
        else:
            self.variance_liters = self.trip.shipped_volume_ambient - self.discharge_volume_ambient

        # 3. نظام كشف التهريب والاشتباه (Flagging System)
        # المعيار القانوني لشركات التوزيع في ليبيا يحدد نسبة فاقد مسموح بها لا تتجاوز 0.5% بسبب النقل والتبخر
        allowed_loss_percentage = Decimal('0.005')
        max_allowed_loss = self.trip.shipped_volume_ambient * allowed_loss_percentage

        # إذا تجاوز الفارق حد الفاقد المسموح به، أو كان الفارق سالباً (إشارة لتلاعب في العدادات) ترفع راية الاشتباه فوراً
        if self.variance_liters > max_allowed_loss or self.variance_liters < Decimal('0'):
            self.is_suspect = True
            self.trip.status = 'arrived'  # تبقى الحالة وصلت ولكن مع تفعيل علم الشبهة للمراقبين
        else:
            self.is_suspect = False
            self.trip.status = 'completed' # رحلة سليمة ومكتملة تماماً

        # تحديث حالة الرحلة الأساسية في جدولها وحفظها
        self.trip.save(update_fields=['status'])

        # 4. حفظ سجل التفريغ كاملاً بالحسابات الجديدة
        super().save(*args, **kwargs)