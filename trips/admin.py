from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Station, Warehouse, Driver, Truck, Trip, DischargeRecord

User = get_user_model()

# 1. تسجيل كيانات المرحلة 1 (المستوى صفر)
admin.site.register(Driver)
admin.site.register(Warehouse)
admin.site.register(Station)

# 2. تسجيل بقية الكيانات العادية
admin.site.register(Truck)
admin.site.register(DischargeRecord)


# 3. تسجيل وتخصيص لوحة تحكم الرحلات (Trip) لمنع ظهور كل المستخدمين
@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        تصفية القوائم المنسدلة في موديل الرحلة بناءً على صلاحيات وأدوار المستخدمين
        """
        # تصفية قائمة موظف المستودع
        if db_field.name == "dispatcher":  # ⚠️ تأكدي أن اسم الحقل في موديل Trip هو 'dispatcher' وليس اسماً آخر
            kwargs["queryset"] = User.objects.filter(role="dispatcher")
            
        # تصفية قائمة مندوب المحطة
        if db_field.name == "agent":       # ⚠️ تأكدي أن اسم الحقل في موديل Trip هو 'agent' وليس اسماً آخر
            kwargs["queryset"] = User.objects.filter(role="agent")
            
        return super().formfield_for_foreignkey(db_field, request, **kwargs)