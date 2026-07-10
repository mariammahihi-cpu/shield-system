from django import forms
from .models import Warehouse
from .models import Station
from .models import DischargeRecord
from faults.models import MechanicalFault
from .models import DischargeRecord, Driver, Warehouse,Truck 


class WarehouseForm(forms.ModelForm):
    """نموذج إنشاء/تعديل المستودع مع تحقّق احترافي."""

    class Meta:
        model = Warehouse
        fields = [
            'warehouse_code', 'warehouse_name', 'location_city',
            'address_details', 'latitude', 'longitude', 'is_active',
        ]
        widgets = {
            'warehouse_code':  forms.TextInput(attrs={'class': 'sh-input', 'placeholder': 'مثال: WH-TRP-01'}),
            'warehouse_name':  forms.TextInput(attrs={'class': 'sh-input', 'placeholder': 'اسم المستودع'}),
            'location_city':   forms.TextInput(attrs={'class': 'sh-input', 'placeholder': 'المدينة'}),
            'address_details': forms.Textarea(attrs={'class': 'sh-input', 'rows': 2, 'placeholder': 'تفاصيل العنوان (اختياري)'}),
            'latitude':        forms.NumberInput(attrs={'class': 'sh-input', 'step': '0.000001', 'placeholder': 'مثال: 32.8872'}),
            'longitude':       forms.NumberInput(attrs={'class': 'sh-input', 'step': '0.000001', 'placeholder': 'مثال: 13.1913'}),
        }

    def clean_warehouse_code(self):
        code = (self.cleaned_data.get('warehouse_code') or '').strip().upper()
        if not code:
            raise forms.ValidationError('رمز المستودع مطلوب.')
        # تحقّق من التفرّد (غير حسّاس لحالة الأحرف) مع استثناء السجل الحالي عند التعديل
        qs = Warehouse.objects.filter(warehouse_code__iexact=code)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('رمز المستودع مستخدم مسبقاً، اختر رمزاً آخر.')
        return code

    def clean_warehouse_name(self):
        name = (self.cleaned_data.get('warehouse_name') or '').strip()
        if len(name) < 3:
            raise forms.ValidationError('اسم المستودع يجب أن يكون 3 أحرف على الأقل.')
        return name

    def clean_latitude(self):
        lat = self.cleaned_data.get('latitude')
        if lat is None or not (-90 <= lat <= 90):
            raise forms.ValidationError('خط العرض يجب أن يكون رقماً بين -90 و 90.')
        return lat

    def clean_longitude(self):
        lon = self.cleaned_data.get('longitude')
        if lon is None or not (-180 <= lon <= 180):
            raise forms.ValidationError('خط الطول يجب أن يكون رقماً بين -180 و 180.')
        return lon



class StationForm(forms.ModelForm):
    """نموذج إنشاء/تعديل المحطة مع تحقّق احترافي."""

    class Meta:
        model = Station
        fields = [
            'customer_number', 'station_name', 'company_branch', 'city',
            'latitude', 'longitude', 'geofence_radius', 'is_active', 'is_banned',
        ]
        widgets = {
            'customer_number': forms.TextInput(attrs={'class': 'sh-input', 'placeholder': 'رقم الزبون'}),
            'station_name':    forms.TextInput(attrs={'class': 'sh-input', 'placeholder': 'اسم المحطة'}),
            'company_branch':  forms.TextInput(attrs={'class': 'sh-input', 'placeholder': 'فرع الشركة'}),
            'city':            forms.TextInput(attrs={'class': 'sh-input', 'placeholder': 'المدينة'}),
            'latitude':        forms.NumberInput(attrs={'class': 'sh-input', 'step': '0.000001', 'placeholder': '32.8872'}),
            'longitude':       forms.NumberInput(attrs={'class': 'sh-input', 'step': '0.000001', 'placeholder': '13.1913'}),
            'geofence_radius': forms.NumberInput(attrs={'class': 'sh-input', 'placeholder': '50'}),
        }

    def clean_customer_number(self):
        num = (self.cleaned_data.get('customer_number') or '').strip()
        if not num:
            raise forms.ValidationError('رقم الزبون مطلوب.')
        qs = Station.objects.filter(customer_number__iexact=num)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('رقم الزبون مستخدم مسبقاً.')
        return num

    def clean_station_name(self):
        name = (self.cleaned_data.get('station_name') or '').strip()
        if len(name) < 3:
            raise forms.ValidationError('اسم المحطة يجب أن يكون 3 أحرف على الأقل.')
        return name

    def clean_latitude(self):
        lat = self.cleaned_data.get('latitude')
        if lat is None or not (-90 <= lat <= 90):
            raise forms.ValidationError('خط العرض يجب أن يكون بين -90 و 90.')
        return lat

    def clean_longitude(self):
        lon = self.cleaned_data.get('longitude')
        if lon is None or not (-180 <= lon <= 180):
            raise forms.ValidationError('خط الطول يجب أن يكون بين -180 و 180.')
        return lon

    def clean_geofence_radius(self):
        r = self.cleaned_data.get('geofence_radius')
        if r is None or r <= 0:
            raise forms.ValidationError('نطاق الأمان يجب أن يكون رقماً موجباً (متر).')
        return r
class DriverForm(forms.ModelForm):
    """نموذج إضافة/تعديل السائق (لمدير النظام) مربوطاً بمستودع معيّن."""

    class Meta:
        model = Driver
        fields = ['driver_name', 'national_id', 'license_number', 'phone_number', 'warehouse', 'is_active']
        widgets = {
            'driver_name':    forms.TextInput(attrs={'class': 'sh-input', 'placeholder': 'الاسم الكامل للسائق'}),
            'national_id':    forms.TextInput(attrs={'class': 'sh-input', 'placeholder': 'الرقم الوطني'}),
            'license_number': forms.TextInput(attrs={'class': 'sh-input', 'placeholder': 'رقم رخصة القيادة'}),
            'phone_number':   forms.TextInput(attrs={'class': 'sh-input', 'placeholder': '09xxxxxxxx'}),
            'warehouse':      forms.Select(attrs={'class': 'sh-input'}),
            'is_active':      forms.CheckboxInput(attrs={'class': 'w-5 h-5 rounded bg-slate-900 border-slate-700'}),
        }
        labels = {
            'driver_name': 'اسم السائق', 'national_id': 'الرقم الوطني',
            'license_number': 'رقم رخصة القيادة', 'phone_number': 'رقم الهاتف',
            'warehouse': 'المستودع التابع له', 'is_active': 'نشط',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['warehouse'].required = True
        self.fields['warehouse'].queryset = Warehouse.objects.filter(is_active=True)
        self.fields['warehouse'].empty_label = '-- اختر المستودع --'

    def clean_phone_number(self):
        value = self.cleaned_data['phone_number'].strip()
        if len(value) < 6:
            raise ValidationError('رقم الهاتف غير صالح.')
        return value
class TruckForm(forms.ModelForm):
    """نموذج إضافة/تعديل الشاحنة (لمدير النظام) مع إسناد سائق نشط."""

    class Meta:
        model = Truck
        fields = ['truck_id', 'driver', 'capacity_liters', 'status', 'last_inspection_date', 'is_gps_active']
        widgets = {
            'truck_id':             forms.TextInput(attrs={'class': 'sh-input', 'placeholder': 'رقم اللوحة'}),
            'driver':               forms.Select(attrs={'class': 'sh-input'}),
            'capacity_liters':      forms.NumberInput(attrs={'class': 'sh-input', 'step': '0.01', 'min': '1', 'placeholder': '40000.00'}),
            'status':               forms.Select(attrs={'class': 'sh-input'}),
            'last_inspection_date': forms.DateInput(attrs={'class': 'sh-input', 'type': 'date'}),
            'is_gps_active':        forms.CheckboxInput(attrs={'class': 'w-5 h-5 rounded bg-slate-900 border-slate-700'}),
        }
        labels = {
            'truck_id': 'رقم اللوحة', 'driver': 'السائق المعيّن',
            'capacity_liters': 'السعة (لتر)', 'status': 'الحالة',
            'last_inspection_date': 'تاريخ آخر فحص', 'is_gps_active': 'جهاز GPS مفعّل',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['driver'].queryset = Driver.objects.filter(is_active=True).order_by('driver_name')
        self.fields['driver'].empty_label = '-- اختر السائق --'

    def clean_capacity_liters(self):
        value = self.cleaned_data['capacity_liters']
        if value <= 0:
            raise ValidationError('السعة يجب أن تكون أكبر من صفر.')
        return value

class DischargeForm(forms.ModelForm):
    # حقل غير مرتبط بالموديل: الأرقام التي شاهدها المندوب فعلياً على الصهريج
    observed_seal_numbers = forms.CharField(
        required=True,
        label='أرقام الأختام المشاهَدة على الصهريج',
        widget=forms.TextInput(attrs={
            'class': 'sh-input',
            'placeholder': 'افصل بفاصلة، مثال: SEAL-4471، SEAL-4472',
        }),
    )

    class Meta:
        model = DischargeRecord
        fields = [
            'discharge_density',
            'discharge_temperature',
            'discharge_volume_ambient',
            'scan_latitude',
            'scan_longitude',
            'seal_notes',                     # ← أضف (اختياري للملاحظات)
        ]
        widgets = {
            'discharge_density': forms.NumberInput(attrs={
                'step': '0.0001', 'min': '0', 'class': 'sh-input', 'placeholder': '0.7450',
            }),
            'discharge_temperature': forms.NumberInput(attrs={
                'step': '0.01', 'min': '-50', 'max': '60', 'class': 'sh-input', 'placeholder': '15.00',
            }),
            'discharge_volume_ambient': forms.NumberInput(attrs={
                'step': '0.01', 'min': '1', 'class': 'sh-input', 'placeholder': '0.00',
            }),
            'scan_latitude': forms.HiddenInput(),
            'scan_longitude': forms.HiddenInput(),
            'seal_notes': forms.Textarea(attrs={     # ← أضف
                'rows': 2, 'class': 'sh-input', 'placeholder': 'ملاحظات إضافية (اختياري)...',
            }),
        }
        labels = {
            'discharge_density': 'الكثافة النوعية المسجلة',
            'discharge_temperature': 'درجة الحرارة عند التفريغ (°C)',
            'discharge_volume_ambient': 'الحجم الفعلي المقاس في المحطة (لتر)',
            'seal_notes': 'ملاحظات الأختام (اختياري)',   # ← أضف
        }

    def __init__(self, *args, trip=None, **kwargs):
        self.trip = trip
        super().__init__(*args, **kwargs)

    def clean_discharge_density(self):
        value = self.cleaned_data['discharge_density']
        if value <= 0:
            raise forms.ValidationError('الكثافة النوعية المسجلة يجب أن تكون أكبر من صفر.')
        return value

    def clean_discharge_volume_ambient(self):
        value = self.cleaned_data['discharge_volume_ambient']
        if value <= 0:
            raise forms.ValidationError('الحجم الفعلي المقاس يجب أن يكون أكبر من صفر.')
        return value


class FaultReportForm(forms.ModelForm):
    """
    نموذج الإبلاغ عن فروقات القراءات أو أعطال الأجهزة (متطلب إدارة البلاغات):
    نوع البلاغ، الوصف، تفاصيل الإجراء، ورفع صورة للعطل. جميع الحقول أعمدة
    موجودة في موديل MechanicalFault.
    """

    class Meta:
        model = MechanicalFault
        fields = [
            'fault_type',
            'description',
            'action_taken',
            'photo',
            'is_critical',
        ]
        widgets = {
            'fault_type': forms.Select(attrs={'class': 'sh-input'}),
            'description': forms.Textarea(attrs={
                'class': 'sh-input', 'rows': 3,
                'placeholder': 'اشرح طبيعة العطل أو فارق القراءات المرصود...',
            }),
            'action_taken': forms.Textarea(attrs={
                'class': 'sh-input', 'rows': 3,
                'placeholder': 'ما الإجراء الميداني الذي اتخذته تجاه هذا العطل؟',
            }),
            'photo': forms.ClearableFileInput(attrs={
                'class': 'sh-input', 'accept': 'image/*',
            }),
            'is_critical': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 rounded bg-slate-900 border-slate-700',
            }),
        }
        labels = {
            'fault_type': 'تصنيف العطل / الفرق المرصود',
            'description': 'وصف العطل أو فارق القراءات',
            'action_taken': 'تفاصيل الإجراء المتخذ',
            'photo': 'صورة توثيقية للعطل',
            'is_critical': 'هل يمنع هذا العطل استمرار التفريغ؟',
        }

    def clean_description(self):
        value = self.cleaned_data['description'].strip()
        if len(value) < 10:
            raise forms.ValidationError('يرجى كتابة وصف تفصيلي لا يقل عن 10 أحرف.')
        return value