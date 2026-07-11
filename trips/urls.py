from django.urls import path
from . import views

app_name = 'trips'

urlpatterns = [
    # ============================================================================
    # 📋 [المجموعة 1: إدارة الرحلات الأساسية]
    # ============================================================================
    # عرض قائمة الرحلات مع تصفية ذكية حسب الدور (dispatcher/agent/manager/auditor/admin)
    path('', views.trip_list, name='trip_list'),
    
    # إنشاء رحلة جديدة (dispatcher/manager/admin فقط)
    path('create/', views.create_trip, name='create_trip'),
    
    # عرض تفاصيل رحلة واحدة مع فحص الصلاحيات المتعددة الطبقات
    path('<int:trip_id>/', views.trip_detail, name='trip_detail'),
    
    # تحديث بيانات الرحلة مع حماية من dispatcher يتجاوز الجيوفينسنج يدويّاً
    path('<int:trip_id>/update/', views.update_trip, name='update_trip'),
    path('trip/<int:trip_id>/depart/', views.mark_trip_departed, name='mark_trip_departed'),
    
    # حذف الرحلة - محمي جداً (manager/admin فقط)
    path('<int:trip_id>/delete/', views.delete_trip, name='delete_trip'),
    
    
    # ============================================================================
    # 🔐 [المجموعة 2: بوابة الحماية وبوابة التفريغ - QR & Discharge Workflow]
    # ============================================================================
    # مسح QR Code الآمن - يستقبل UUID Token وليس ID عادي (حماية من Enumeration)
    # التدفق: يتحقق من صلاحية QR → يسجل qr_scanned_at → يوجه للتفريغ
    # Security: يمنع التفريغ المباشر بدون مسح QR
    path('qr/<uuid:qr_token>/', views.qr_redirect, name='qr_redirect'),
    
    # تقديم فورم التفريغ الميداني مع Geofencing و حساب العجز والاشتباه
    # يتحقق من: صلاحيات المندوب + مسح QR السابق + حالة الرحلة + صحة البيانات الرقمية
    # الحسابات: Haversine (المسافة) + Thermal Correction (الحجم) + Variance (العجز)
    path('<int:trip_id>/discharge/', views.submit_discharge, name='submit_discharge'),
    
    # عرض سجلات التفريغ التاريخية مع تصفية حسب الدور
    # agent: يرى سجلاته فقط | dispatcher/manager/auditor/admin: يرى كل السجلات
    path('discharge-records/', views.discharge_records, name='discharge_records'),
    
    
    # ============================================================================
    # 🚨 [المجموعة 3: الأمن والتدقيق والتقارير - Tamper Detection & Analytics]
    # ============================================================================
    # عرض الشحنات المشبوهة فقط - كشف التلاعب والشذوذ
    # معايير الاشتباه: عجز > 0.5% أو خارج النطاق الجغرافي أو أختام غير مطابقة
    # dispatcher/agent: يرى رحلاتهم المشبوهة | manager/auditor/admin: يرى كل المشبوهة
    path('suspect/', views.suspect_trips, name='suspect_trips'),
    
    # لوحة تحكم التقارير والإحصائيات الشاملة
    # المحتوى: إجمالي الرحلات + الحالات + نسب العجز + الشحنات المشبوهة + أداء المندوبين
    # الصلاحيات: dispatcher/manager/auditor/admin
    path('reports/', views.trip_reports, name='trip_reports'),
    
    # التقرير المفصل لرحلة واحدة
    # يتضمن: بيانات الرحلة + سجل التفريغ الكامل + جميع الحسابات + حالة الاشتباه وأسبابها
    # الصلاحيات: dispatcher/manager/auditor/admin
    path('<int:trip_id>/report/', views.trip_report_detail, name='trip_report_detail'),
    path('trip/<int:trip_id>/depart/', views.mark_trip_departed, name='mark_trip_departed'),
    path('monitoring/map/', views.shipments_map, name='shipments_map'),
    
    
    # ============================================================================
    # 📍 [المجموعة 4: البيانات الأساسية للقراءة - Master Data (Read-Only)]
    # ============================================================================
        # ===== إدارة المحطات (Master Data — admin) =====
    path('stations/',                 views.stations_list,  name='stations_list'),
    path('stations/create/',          views.station_create, name='station_create'),
    path('stations/<int:pk>/edit/',   views.station_update, name='station_update'),
    path('stations/<int:pk>/archive/', views.station_archive, name='station_archive'),
    
    # عرض قائمة المستودعات المركزية النشطة
    # dispatcher: يرى المستودعات المعينة له فقط | manager/auditor/admin: يرى كل المستودعات
    # لا يوجد CRUD - الإدارة الكاملة من Django Admin
        # ===== إدارة المستودعات (Master Data — admin) =====
    path('warehouses/',                 views.warehouse_list,   name='warehouse_list'),
    path('warehouses/create/',          views.warehouse_create, name='warehouse_create'),
    path('warehouses/<int:pk>/edit/',   views.warehouse_update, name='warehouse_update'),
    path('warehouses/<int:pk>/archive/', views.warehouse_archive, name='warehouse_archive'),
    #agent
    path('agent/', views.agent_trip_list, name='agent_trip_list'),
    path('agent/discharge-log/', views.agent_discharge_log, name='discharge_log'),
    path('agent/faults/', views.agent_fault_list, name='agent_fault_list'),
    path('agent/faults/<int:pk>/', views.agent_fault_detail, name='agent_fault_detail'),
    path('agent/trip/<int:trip_id>/discharge/', views.submit_discharge, name='submit_discharge'),
    path('agent/trip/<int:trip_id>/report-fault/', views.report_fault, name='report_fault'),
    path('drivers/', views.driver_list, name='driver_list'),
    path('drivers/create/', views.driver_create, name='driver_create'),
    path('drivers/<int:pk>/edit/', views.driver_update, name='driver_update'),
    path('drivers/<int:pk>/archive/', views.driver_archive, name='driver_archive'),
    path('trucks/', views.truck_list, name='truck_list'),
    path('trucks/create/', views.truck_create, name='truck_create'),
    path('trucks/<int:pk>/edit/', views.truck_update, name='truck_update'),
    path('trucks/<int:pk>/archive/', views.truck_archive, name='truck_archive'),
    path('<int:trip_id>/qr/', views.trip_qr, name='trip_qr'),
]