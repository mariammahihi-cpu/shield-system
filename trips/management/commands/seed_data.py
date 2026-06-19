from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
from trips.models import Station, Warehouse, Driver, Truck, Trip, DischargeRecord
from alerts.models import Alert

User = get_user_model()


class Command(BaseCommand):
    help = 'حقن بيانات تجريبية للنظام (آمنة - لا تحذف البيانات الموجودة)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔧 جاري حقن البيانات التجريبية...'))

        try:
            self.stdout.write('\n📍 جاري إنشاء المحطات...')
            stations = self._create_stations()

            self.stdout.write('\n📦 جاري إنشاء المستودعات...')
            warehouses = self._create_warehouses()

            self.stdout.write('\n👨‍✈️ جاري إنشاء السائقين...')
            drivers = self._create_drivers()

            self.stdout.write('\n🚛 جاري إنشاء الشاحنات...')
            trucks = self._create_trucks(drivers)

            self.stdout.write('\n👥 جاري إنشاء المستخدمين...')
            users = self._create_users()

            self.stdout.write('\n🔗 جاري ربط الموظفين بالمستودعات...')
            self._assign_employees_to_warehouses(warehouses, users)

            self.stdout.write('\n🔗 جاري ربط المندوبين بالمحطات...')
            self._assign_agents_to_stations(stations, users)

            self.stdout.write('\n✈️ جاري إنشاء رحلات تجريبية...')
            trips = self._create_trips(users, trucks, stations, warehouses)

            self.stdout.write('\n📋 جاري إنشاء سجلات التفريغ...')
            self._create_discharge_records(trips, users)

            self.stdout.write(self.style.SUCCESS('\n✅ اكتملت عملية حقن البيانات بنجاح!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ خطأ: {str(e)}'))
            raise

    def _create_stations(self):
        stations_data = [
            {
                'customer_number': 'STN-001',
                'station_name': 'محطة الخليج الرئيسية',
                'company_branch': 'فرع طرابلس',
                'city': 'طرابلس',
                'latitude': Decimal('32.8872'),
                'longitude': Decimal('13.1913'),
                'geofence_radius': 50,
            },
            {
                'customer_number': 'STN-002',
                'station_name': 'محطة البريقة',
                'company_branch': 'فرع بنغازي',
                'city': 'بنغازي',
                'latitude': Decimal('32.1167'),
                'longitude': Decimal('20.0667'),
                'geofence_radius': 75,
            },
            {
                'customer_number': 'STN-003',
                'station_name': 'محطة الكفرة',
                'company_branch': 'فرع الجنوب',
                'city': 'الكفرة',
                'latitude': Decimal('24.2155'),
                'longitude': Decimal('21.2589'),
                'geofence_radius': 100,
            },
        ]

        stations = {}
        for data in stations_data:
            station, created = Station.objects.get_or_create(
                customer_number=data['customer_number'],
                defaults=data
            )
            status = '✅ جديد' if created else 'ℹ️  موجود'
            self.stdout.write(f'  {status}: {station.station_name}')
            stations[data['customer_number']] = station

        return stations

    def _create_warehouses(self):
        warehouses_data = [
            {
                'warehouse_code': 'WH-001',
                'warehouse_name': 'مستودع طرابلس الرئيسي',
                'location_city': 'طرابلس',
                'address_details': 'شارع العزيزية، بجانب ميناء طرابلس',
            },
            {
                'warehouse_code': 'WH-002',
                'warehouse_name': 'مستودع بنغازي',
                'location_city': 'بنغازي',
                'address_details': 'منطقة الكويفية، شرق المدينة',
            },
        ]

        warehouses = {}
        for data in warehouses_data:
            warehouse, created = Warehouse.objects.get_or_create(
                warehouse_code=data['warehouse_code'],
                defaults=data
            )
            status = '✅ جديد' if created else 'ℹ️  موجود'
            self.stdout.write(f'  {status}: {warehouse.warehouse_name}')
            warehouses[data['warehouse_code']] = warehouse

        return warehouses

    def _create_drivers(self):
        drivers_data = [
            {
                'national_id': 'ID-001',
                'driver_name': 'محمد علي الفيتوري',
                'license_number': 'LIC-001',
                'phone_number': '218911234567',
            },
            {
                'national_id': 'ID-002',
                'driver_name': 'أحمد محمود الجبري',
                'license_number': 'LIC-002',
                'phone_number': '218922234567',
            },
            {
                'national_id': 'ID-003',
                'driver_name': 'عمر الشريف',
                'license_number': 'LIC-003',
                'phone_number': '218933234567',
            },
        ]

        drivers = {}
        for data in drivers_data:
            driver, created = Driver.objects.get_or_create(
                national_id=data['national_id'],
                defaults=data
            )
            status = '✅ جديد' if created else 'ℹ️  موجود'
            self.stdout.write(f'  {status}: {driver.driver_name}')
            drivers[data['national_id']] = driver

        return drivers

    def _create_trucks(self, drivers):
        trucks_data = [
            {
                'truck_id': 'TRUCK-001',
                'driver': drivers.get('ID-001'),
                'capacity_liters': Decimal('30000.00'),
                'last_inspection_date': datetime.now().date(),
            },
            {
                'truck_id': 'TRUCK-002',
                'driver': drivers.get('ID-002'),
                'capacity_liters': Decimal('25000.00'),
                'last_inspection_date': datetime.now().date(),
            },
            {
                'truck_id': 'TRUCK-003',
                'driver': drivers.get('ID-003'),
                'capacity_liters': Decimal('35000.00'),
                'last_inspection_date': datetime.now().date(),
            },
        ]

        trucks = {}
        for data in trucks_data:
            if data['driver'] is None:
                self.stdout.write(f'  ⚠️  تخطي {data["truck_id"]}: لا يوجد سائق')
                continue

            truck, created = Truck.objects.get_or_create(
                truck_id=data['truck_id'],
                defaults=data
            )
            status = '✅ جديد' if created else 'ℹ️  موجود'
            self.stdout.write(f'  {status}: {truck.truck_id}')
            trucks[data['truck_id']] = truck

        return trucks

    def _create_users(self):
        users_data = [
            {
                'username': 'dispatcher_ahmed',
                'email': 'dispatcher@shield.local',
                'first_name': 'أحمد',
                'last_name': 'محمود',
                'password': 'dispatcher123',
                'role': 'dispatcher',
            },
            {
                'username': 'agent_fatima',
                'email': 'agent@shield.local',
                'first_name': 'فاطمة',
                'last_name': 'علي',
                'password': 'agent123',
                'role': 'agent',
            },
            {
                'username': 'agent_salim',
                'email': 'agent2@shield.local',
                'first_name': 'سالم',
                'last_name': 'محمد',
                'password': 'agent123',
                'role': 'agent',
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
                status = '✅ جديد'
            else:
                status = 'ℹ️  موجود'
            self.stdout.write(f'  {status}: {user.username} ({user.role})')
            users[data['username']] = user

        return users

    def _assign_employees_to_warehouses(self, warehouses, users):
        dispatcher = users.get('dispatcher_ahmed')
        if not dispatcher:
            self.stdout.write('  ⚠️  لا يوجد موظف مستودع')
            return

        for warehouse in warehouses.values():
            warehouse.employees.add(dispatcher)
            self.stdout.write(f'  ✅ ربط: {dispatcher.username} → {warehouse.warehouse_name}')

    def _assign_agents_to_stations(self, stations, users):
        agent1 = users.get('agent_fatima')
        agent2 = users.get('agent_salim')

        if not agent1 or not agent2:
            self.stdout.write('  ⚠️  لا يوجد مندوبين كافيين')
            return

        for idx, station in enumerate(stations.values()):
            agent = agent1 if idx % 2 == 0 else agent2
            station.agents.add(agent)
            self.stdout.write(f'  ✅ ربط: {agent.username} → {station.station_name}')

    def _create_trips(self, users, trucks, stations, warehouses):
        dispatcher = users.get('dispatcher_ahmed')
        agent1 = users.get('agent_fatima')
        agent2 = users.get('agent_salim')

        if not all([dispatcher, agent1, agent2]):
            self.stdout.write('  ⚠️  بيانات ناقصة')
            return []

        trips_data = [
            {
                'dispatcher': dispatcher,
                'agent': agent1,
                'truck': list(trucks.values())[0],
                'station': list(stations.values())[0],
                'warehouse': list(warehouses.values())[0],
                'seal_numbers': '5501,5502,5503',
                'shipped_volume_ambient': Decimal('15000.00'),
                'shipped_temperature': Decimal('35.5'),
                'shipped_density': Decimal('0.8450'),
            },
            {
                'dispatcher': dispatcher,
                'agent': agent2,
                'truck': list(trucks.values())[1] if len(trucks) > 1 else list(trucks.values())[0],
                'station': list(stations.values())[1] if len(stations) > 1 else list(stations.values())[0],
                'warehouse': list(warehouses.values())[1] if len(warehouses) > 1 else list(warehouses.values())[0],
                'seal_numbers': '6601,6602,6603',
                'shipped_volume_ambient': Decimal('20000.00'),
                'shipped_temperature': Decimal('32.0'),
                'shipped_density': Decimal('0.8500'),
            },
        ]

        trips = []
        for idx, data in enumerate(trips_data):
            trip_code = f'SHIELD-TEST-{idx + 1:03d}'
            trip, created = Trip.objects.get_or_create(
                trip_code=trip_code,
                defaults=data
            )
            status = '✅ جديد' if created else 'ℹ️  موجود'
            self.stdout.write(f'  {status}: {trip.trip_code}')
            trips.append(trip)

        return trips

    def _create_discharge_records(self, trips, users):
        agent = users.get('agent_fatima')

        if not agent or not trips:
            self.stdout.write('  ⚠️  بيانات ناقصة')
            return

        for trip in trips:
            if DischargeRecord.objects.filter(trip=trip).exists():
                self.stdout.write(f'  ℹ️  موجود: سجل تفريغ {trip.trip_code}')
                continue

            discharge = DischargeRecord.objects.create(
                trip=trip,
                agent=agent,
                discharge_volume_ambient=Decimal('14900.00'),
                discharge_temperature=Decimal('32.0'),
                discharge_density=Decimal('0.8465'),
                seal_check_passed=True,
                seal_notes='جميع الأختام سليمة',
                scan_latitude=trip.station.latitude,
                scan_longitude=trip.station.longitude,
            )
            self.stdout.write(f'  ✅ جديد: سجل تفريغ {trip.trip_code}')