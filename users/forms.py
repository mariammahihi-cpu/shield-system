from django import forms
from django.contrib.auth.password_validation import validate_password
from .models import User
from trips.models import Warehouse, Station
from django import forms
from django.core.exceptions import ValidationError
from .models import SystemSettings

class AdminUserCreationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'sh-input'}),
        validators=[validate_password], label="كلمة المرور",
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'sh-input'}),
        label="تأكيد كلمة المرور",
    )

    # حقول الربط الشرطية (غير إلزامية على مستوى النموذج، نتحقّق في clean)
    warehouses = forms.ModelMultipleChoiceField(
        queryset=Warehouse.objects.filter(is_active=True), required=False,
        widget=forms.SelectMultiple(attrs={'class': 'sh-input', 'id': 'id_warehouses'}),
        label="المستودعات المرتبطة",
    )
    station = forms.ModelChoiceField(
        queryset=Station.objects.filter(is_active=True, is_banned=False), required=False,
        widget=forms.Select(attrs={'class': 'sh-input', 'id': 'id_station'}),
        label="المحطة المرتبطة",
    )

    class Meta:
        model = User
        fields = ['username', 'full_name', 'national_id', 'phone_number', 'role']
        widgets = {f: forms.TextInput(attrs={'class': 'sh-input'}) for f in
                   ['username', 'full_name', 'national_id', 'phone_number']}
        widgets['role'] = forms.Select(attrs={'class': 'sh-input', 'id': 'id_role'})

    # ===== إلزام الحقول الجديدة =====
    def clean_national_id(self):
        v = (self.cleaned_data.get('national_id') or '').strip()
        if not v:
            raise forms.ValidationError('الرقم الوطني إجباري.')
        return v

    def clean_phone_number(self):
        v = (self.cleaned_data.get('phone_number') or '').strip()
        if not v:
            raise forms.ValidationError('رقم الهاتف إجباري.')
        return v

    # ===== التحقّق العام (تطابق كلمة المرور + الربط الشرطي) =====
    def clean(self):
        cleaned = super().clean()

        # 1) تطابق كلمتي المرور (تحقّق خلفي آمن)
        pw, pw2 = cleaned.get('password'), cleaned.get('password_confirm')
        if pw and pw2 and pw != pw2:
            self.add_error('password_confirm', 'كلمتا المرور غير متطابقتين.')

        # 2) الربط الشرطي حسب الدور
        role = cleaned.get('role')
        if role == 'dispatcher' and not cleaned.get('warehouses'):
            self.add_error('warehouses', 'موظف المستودع يجب ربطه بمستودع واحد على الأقل.')
        if role == 'agent' and not cleaned.get('station'):
            self.add_error('station', 'مندوب المحطة يجب ربطه بمحطة.')

        return cleaned

    # ===== الحفظ + الربط عبر M2M =====
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            if user.role == 'dispatcher':
                user.assigned_warehouses.set(self.cleaned_data['warehouses'])
            elif user.role == 'agent':
                user.assigned_stations.set([self.cleaned_data['station']])
        return user
#الاعدادات التشغيلية
class SystemSettingsForm(forms.ModelForm):
    class Meta:
        model = SystemSettings
        fields = ['password_validity_days', 'max_login_attempts',
                  'default_geofence_radius', 'variance_alert_threshold', 'enable_alerts']
        widgets = {
            'password_validity_days':   forms.NumberInput(attrs={'class': 'sh-input'}),
            'max_login_attempts':       forms.NumberInput(attrs={'class': 'sh-input'}),
            'default_geofence_radius':  forms.NumberInput(attrs={'class': 'sh-input'}),
            'variance_alert_threshold': forms.NumberInput(attrs={'class': 'sh-input', 'step': '0.1'}),
        }

    def clean_max_login_attempts(self):
        v = self.cleaned_data['max_login_attempts']
        if not (1 <= v <= 10):
            raise ValidationError('يجب أن تكون بين 1 و 10.')
        return v