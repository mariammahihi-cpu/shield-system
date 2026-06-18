"""
Setup Script for Shield System - Idempotent Data Creation
يعمل بدون أخطاء حتى لو تم تشغيله أكثر من مرة
"""

import os
import django
import sys
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shield_core.settings')
django.setup()

# Import Models
from django.contrib.auth import get_user_model
from django.utils import timezone
from trips.models import Station, Warehouse, Driver, Truck, Trip, DischargeRecord
from alerts.models import Alert

User = get_user_model()

# ==================== UTILITY FUNCTIONS ====================

def print_header(title):
    """طباعة رأس القسم"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_success(message):
    """طباعة رسالة نجاح"""
    print(f"✅ {message}")

def print_info(message):
    """طباعة رسالة معلومات"""
    print(f"ℹ️  {message}")

def print_error(message):
    """طباعة رسالة خطأ"""
    print(f"❌ {message}")

# ==================== CREATION FUNCTIONS ====================

def create_users():
    """إنشاء المستخدمين الأساسيين (Idempotent)"""
    print_header("👤 إنشاء المستخدمين")
    
    users_data = [
        {
            'username': 'admin',
            'email': 'admin@shield.ly',
            'full_name': 'مدير النظام',
            'role': 'admin',
            'password': 'admin123456'
        },
        {
            'username': 'dispatcher1',
            'email': 'dispatcher@shield.ly',
            'full_name': 'موظف المستودع الأول',
            'role': 'dispatcher',
            'password': 'dispatcher123'
        },
        {
            'username': 'agent1',
            'email': 'agent@shield.ly',
            'full_name': 'مندوب المحطة الأول',
            'role': 'agent',
            'password': 'agent123'
        },
    ]
    
    users = {}
    for data in users_data:
        password = data.pop('password')
        user, created = User.objects.get_or_create(
            username=data['username'],
            defaults=data
        )
        
        if created:
            user.set_password(password)
            user.save()
            print_success(f"تم إنشاء المستخدم: {user.full_name}")
        else:
            print_info(f"المستخدم موجود بالفعل: {user.full_name}")
        
        users[data['username']] = user
    
    return users

def create_stations():
    """إنشاء المحطات (Idempotent)"""
    print_header("🏢 إنشاء المحطات")
    
    stations_data = [
        {
            'customer_number': 'STA-001',
            'station_name': 'محطة البنزين الرئيسية',
            'company_branch': 'فرع طرابلس الرئيسي',
            'city': 'طرابلس',
            'latitude': Decimal('32.8872'),
            'longitude': Decimal('13.1913'),
            'geofence_radius': 50,  # متر
            'is_active': True,
            'is_banned': False,
        },
        {
            'customer_number': 'STA-002',
            'station_name': 'محطة الديزل الثانوية',
            'company_branch': 'فرع طرابلس الثاني',
            'city': 'طرابلس',
            'latitude': Decimal('32.8900'),
            'longitude': Decimal('13.2000'),
            'geofence_radius': 75,
            'is_active': True,
            'is_banned': False,
        },
        {
            'customer_number': 'STA-003',
            'station_name': 'محطة الغاز الثالثة',
            'company_branch': 'فرع الخمس',
            'city': 'الخمس',
            'latitude': Decimal('32.6500'),
            'longitude': Decimal('14.2800'),
            'geofence_radius': 100,
            'is_active': True,
            'is_banned': False,
        },
    ]
    
    stations = []
    for data in stations_data:
        station, created = Station.objects.get_or_create(
            customer_number=data['customer_number'],
            defaults=data
        )
        
        if created:
            print_success(f"تم إنشاء المحطة: {station.station_name} (نطاق: {station.geofence_radius}م)")
        else:
            print_info(f"المحطة موجودة بالفعل: {station.station_name}")
        
        stations.append(station)
    
    return stations

def create_warehouses():
    """إنشاء المستودعات (Idempotent)"""
    print_header("📦 إنشاء المستودعات")
    
    warehouses_data = [
        {
            'warehouse_code': 'WH-001',
            'warehouse_name': 'مستودع الوقود الرئيسي',
            'location_city': 'طرابلس',
            'address_details': 'شارع الخليج، المبنى الأول، بجانب الميناء',
            'is_active': True,
        },
        {
            'warehouse_code': 'WH-002',
            'warehouse_name': 'مستودع الديزل الاحتياطي',
            'location_city': 'الخمس',
            'address_details': 'شارع النيل، المبنى الثاني، قرب المحطة',
            'is_active': True,
        },
    ]
    
    warehouses = []
    for data in warehouses_data:
        warehouse, created = Warehouse.objects.get_or_create(
            warehouse_code=data['warehouse_code'],
            defaults=data
        )
        
        if created:
            print_success(f"تم إنشاء المستودع: {warehouse.warehouse_name}")
        else:
            print_info(f"المستودع موجود بالفعل: {warehouse.warehouse_name}")
        
        warehouses.append(warehouse)
    
    return warehouses

def create_drivers():
    """إنشاء السائقين (Idempotent)"""
    print_header("🚗 إنشاء السائقين")
    
    drivers_data = [
        {
            'national_id': '120000001',
            'driver_name': 'أحمد محمد علي',
            'license_number': 'DL-2024-001',
            'phone_number': '0912345678',
            'is_active': True,
        },
        {
            'national_id': '120000002',
            'driver_name': 'محمد علي حسن',
            'license_number': 'DL-2024-002',
            'phone_number': '0912345679',
            'is_active': True,
        },
        {
            'national_id': '120000003',
            'driver_name': 'علي حسن محمود',
            'license_number': 'DL-2024-003',
            'phone_number': '0912345680',
            'is_active': True,
        },
    ]
    
    drivers = []
    for data in drivers_data:
        driver, created = Driver.objects.get_or_create(
            national_id=data['national_id'],
            defaults=data
        )
        
        if created:
            print_success(f"تم إنشاء السائق: {driver.driver_name}")
        else:
            print_info(f"السائق موجود بالفعل: {driver.driver_name}")
        
        drivers.append(driver)
    
    return drivers

def create_trucks(drivers):
    """إنشاء الشاحنات (Idempotent)"""
    print_header("🚙 إنشاء الشاحنات")
    
    trucks_data = [
        {
            'truck_id': 'TRK-001',
            'driver': drivers[0],
            'capacity_liters': Decimal('5000.00'),
            'status': 'active',
            'last_inspection_date': timezone.now().date(),
            'is_gps_active': True,
        },
        {
            'truck_id': 'TRK-002',
            'driver': drivers[1],
            'capacity_liters': Decimal('3500.00'),
            'status': 'active',
            'last_inspection_date': timezone.now().date(),
            'is_gps_active': True,
        },
        {
            'truck_id': 'TRK-003',
            'driver': drivers[2],
            'capacity_liters': Decimal('4000.00'),
            'status': 'active',
            'last_inspection_date': timezone.now().date(),
            'is_gps_active': True,
        },
    ]
    
    trucks = []
    for data in trucks_data:
        truck, created = Truck.objects.get_or_create(
            truck_id=data['truck_id'],
            defaults=data
        )
        
        if created:
            print_success(f"تم إنشاء الشاحنة: {truck.truck_id} (سائق: {truck.driver.driver_name})")
        else:
            print_info(f"الشاحنة موجودة بالفعل: {truck.truck_id}")
        
        trucks.append(truck)
    
    return trucks

def create_trips(users, stations, warehouses, trucks):
    """إنشاء الرحلات (Idempotent)"""
    print_header("✈️  إنشاء الرحلات")
    
    trips = []
    for i in range(5):
        trip_data = {
            'dispatcher': users['dispatcher1'],
            'agent': users['agent1'],
            'truck': trucks[i % len(trucks)],
            'station': stations[i % len(stations)],
            'warehouse': warehouses[i % len(warehouses)],
            'fuel_type': 'petrol',
            'seal_numbers': f'SEAL-{i+1:03d},SEAL-{i+1:03d}-A,SEAL-{i+1:03d}-B',
            'shipped_volume_ambient': Decimal('4500.00'),
            'shipped_temperature': Decimal('25.50'),
            'shipped_density': Decimal('0.8500'),
            'status': 'in_transit' if i % 2 == 0 else 'arrived',
            'notes': f'رحلة تجريبية #{i+1}',
        }
        
        trip, created = Trip.objects.get_or_create(
            trip_code=f'SHIELD-{i+1:04d}',
            defaults=trip_data
        )
        
        if created:
            print_success(f"تم إنشاء الرحلة: {trip.trip_code} → {trip.station.station_name}")
        else:
            print_info(f"الرحلة موجودة بالفعل: {trip.trip_code}")
        
        trips.append(trip)
    
    return trips

def create_discharge_records(trips, users):
    """إنشاء سجلات التفريغ (Idempotent)"""
    print_header("📝 إنشاء سجلات التفريغ")
    
    for i, trip in enumerate(trips):
        # رحلة مشبوهة كل 3 رحلات (عجز أكثر من 0.5%)
        if i % 3 == 0:
            discharge_volume = Decimal('4200.00')  # عجز 300 لتر (6.67%)
            is_suspect = True
            notes = "⚠️ عجز مشبوه - يحتاج تحقيق"
        else:
            discharge_volume = Decimal('4485.00')  # عجز 15 لتر (0.33%)
            is_suspect = False
            notes = "✅ ضمن النسبة المسموحة"
        
        discharge, created = DischargeRecord.objects.get_or_create(
            trip=trip,
            defaults={
                'agent': users['agent1'],
                'discharge_volume_ambient': discharge_volume,
                'discharge_temperature': Decimal('22.00'),
                'discharge_density': Decimal('0.8550'),
                'scan_latitude': trip.station.latitude,
                'scan_longitude': trip.station.longitude,
                'scan_distance_m': Decimal('0'),  # داخل النطاق
                'geofence_status': 'green',
                'seal_check_passed': True,
                'seal_notes': 'جميع الأختام سليمة',
                'notes': notes,
            }
        )
        
        if created:
            status = "🚨 مشبوهة" if discharge.is_suspect else "✅ سليمة"
            variance = f"{discharge.variance_liters} لتر ({discharge.variance_percent}%)"
            print_success(f"تم إنشاء سجل تفريغ: {trip.trip_code} ({status}) - العجز: {variance}")
        else:
            print_info(f"سجل التفريغ موجود: {trip.trip_code}")

def create_alerts(trips):
    """إنشاء الإنذارات التلقائية (Idempotent)"""
    print_header("⚠️  إنشاء الإنذارات")
    
    alerts_created = 0
    for trip in trips:
        # تحقق إذا كان هناك سجل تفريغ مشبوه
        if hasattr(trip, 'discharge_record') and trip.discharge_record.is_suspect:
            alert, created = Alert.objects.get_or_create(
                trip=trip,
                alert_type='volume_variance',
                defaults={
                    'severity': 'critical',
                    'description': (
                        f"🚨 عجز حرج في الرحلة {trip.trip_code}\n"
                        f"العجز: {trip.discharge_record.variance_liters} لتر "
                        f"({trip.discharge_record.variance_percent}%)\n"
                        f"المحطة: {trip.station.station_name}"
                    ),
                    'is_resolved': False,
                }
            )
            
            if created:
                print_success(f"تم إنشاء إنذار: {trip.trip_code} - {alert.get_severity_display()}")
                alerts_created += 1
            else:
                print_info(f"الإنذار موجود: {trip.trip_code}")
    
    if alerts_created == 0:
        print_info("لا توجد رحلات مشبوهة - لم يتم إنشاء إنذارات جديدة")

# ==================== STATISTICS ====================

def print_statistics():
    """طباعة الإحصائيات النهائية"""
    print_header("📊 الإحصائيات النهائية")
    
    stats = {
        '👤 المستخدمون': User.objects.count(),
        '🏢 المحطات': Station.objects.count(),
        '📦 المستودعات': Warehouse.objects.count(),
        '🚗 السائقون': Driver.objects.count(),
        '🚙 الشاحنات': Truck.objects.count(),
        '✈️  الرحلات': Trip.objects.count(),
        '📝 سجلات التفريغ': DischargeRecord.objects.count(),
        '⚠️  الإنذارات النشطة': Alert.objects.filter(is_resolved=False).count(),
        '✅ الإنذارات المحلولة': Alert.objects.filter(is_resolved=True).count(),
    }
    
    for label, count in stats.items():
        print(f"{label}: {count}")

# ==================== MAIN FUNCTION ====================

def main():
    """الدالة الرئيسية"""
    try:
        print("\n" + "="*60)
        print("  🚀 Shield System - Data Setup Script")
        print("  Idempotent (آمن لإعادة التشغيل)")
        print("="*60)
        
        # إنشاء البيانات
        users = create_users()
        stations = create_stations()
        warehouses = create_warehouses()
        drivers = create_drivers()
        trucks = create_trucks(drivers)
        trips = create_trips(users, stations, warehouses, trucks)
        create_discharge_records(trips, users)
        create_alerts(trips)
        
        # الإحصائيات
        print_statistics()
        
        print("\n" + "="*60)
        print("  ✅ تمت جميع العمليات بنجاح!")
        print("  🎉 السكربت آمن لإعادة التشغيل (Idempotent)")
        print("  📱 جرّب المسارات:")
        print("     - http://127.0.0.1:8000/")
        print("     - http://127.0.0.1:8000/admin/")
        print("     - http://127.0.0.1:8000/trips/")
        print("="*60 + "\n")
        
        return 0
        
    except Exception as e:
        print_error(f"حدث خطأ: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())