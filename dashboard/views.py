from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
import json
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404


@login_required
def home(request):
    role = request.user.role
    redirect_map = {
        'admin':      'dashboard:admin_dashboard',
        'dispatcher': 'dashboard:dispatcher_dashboard',
        'driver':     'dashboard:driver_dashboard',
        'agent':      'dashboard:agent_dashboard',
        'auditor':    'dashboard:auditor_dashboard',
        'manager':    'dashboard:manager_dashboard',
    }
    target = redirect_map.get(role, 'users:login')
    return redirect(target)


@login_required
def admin_dashboard(request):
    if request.user.role != 'admin':
        return redirect('dashboard:home')
    from users.models import User
    from trips.models import Trip
    context = {
        'total_users':   User.objects.count(),
        'locked_users':  User.objects.filter(is_locked=True).count(),
        'users_by_role': User.objects.values('role').annotate(count=Count('id')),
        'recent_users':  User.objects.order_by('-date_joined')[:10],
    }
    return render(request, 'dashboard/admin_dashboard.html', context)


@login_required
def dispatcher_dashboard(request):
    if request.user.role != 'dispatcher':
        return redirect('dashboard:home')
    from trips.models import Trip
    my_trips = Trip.objects.filter(dispatcher=request.user)
    context = {
        'active_trips':    my_trips.filter(status__in=['created', 'in_transit', 'arrived']).count(),
        'completed_trips': my_trips.filter(status='completed').count(),
        'recent_trips':    my_trips.order_by('-created_at')[:5],
    }
    return render(request, 'dashboard/dispatcher_dashboard.html', context)


@login_required
def driver_dashboard(request):
    if request.user.role != 'driver':
        return redirect('dashboard:home')
    from trips.models import Trip
    my_trips = Trip.objects.filter(driver=request.user)
    context = {
        'active_trip':     my_trips.filter(status__in=['created', 'in_transit', 'arrived']).first(),
        'completed_trips': my_trips.filter(status='completed').count(),
        'recent_trips':    my_trips.order_by('-created_at')[:5],
    }
    return render(request, 'dashboard/driver_dashboard.html', context)


@login_required
def agent_dashboard(request):
    if request.user.role != 'agent':
        return redirect('dashboard:home')
    from trips.models import Trip
    my_trips = Trip.objects.filter(agent=request.user)
    context = {
        'pending_trips':   my_trips.filter(status='arrived').count(),
        'completed_trips': my_trips.filter(status='completed').count(),
        'recent_trips':    my_trips.order_by('-created_at')[:5],
    }
    return render(request, 'dashboard/agent_dashboard.html', context)


@login_required
def auditor_dashboard(request):
    if request.user.role != 'auditor':
        return redirect('dashboard:home')
    from alerts.models import Alert
    now = timezone.now()
    week_ago = now - timedelta(days=7)
    context = {
        'open_alerts':     Alert.objects.filter(is_resolved=False).count(),
        'critical_alerts': Alert.objects.filter(is_resolved=False, severity='critical').count(),
        'recent_alerts':   Alert.objects.filter(is_resolved=False).order_by('-created_at')[:10],
        'weekly_alerts':   Alert.objects.filter(created_at__gte=week_ago).count(),
        'geofence_alerts': Alert.objects.filter(is_resolved=False, alert_type='geofence_violation').count(),
        'volume_alerts':   Alert.objects.filter(is_resolved=False, alert_type='volume_variance').count(),
    }
    return render(request, 'dashboard/auditor_dashboard.html', context)


@login_required
def manager_dashboard(request):
    if request.user.role != 'manager':
        return redirect('dashboard:home')

    from django.db.models import Count, Sum, Avg, Q
    from trips.models import Trip, Station, DischargeRecord
    from alerts.models import Alert
    from faults.models import MechanicalFault

    # إجمالي العجز والفقد + متوسط نسبة العجز
    agg = DischargeRecord.objects.aggregate(
        total_loss=Sum('variance_liters'),
        avg_variance=Avg('variance_percent'),
    )
    total_loss = agg['total_loss'] or 0
    avg_variance = agg['avg_variance'] or 0

    # مؤشرات المحطات: عدد الشحنات + المشبوهة لكل محطة
    station_stats = (
        Station.objects.annotate(
            trips_count=Count('trip', distinct=True),
            suspect_count=Count('trip', filter=Q(trip__status='suspect'), distinct=True),
        ).order_by('-suspect_count', '-trips_count')[:10]
    )

    context = {
        'total_trips':      Trip.objects.count(),
        'completed_trips':  Trip.objects.filter(status='completed').count(),
        'suspect_trips':    Trip.objects.filter(status='suspect').count(),
        'pending_trips':    Trip.objects.filter(status='pending').count(),
        'in_transit_trips': Trip.objects.filter(status='in_transit').count(),
        'total_loss':       round(float(total_loss), 2),
        'avg_variance':     round(float(avg_variance), 3),
        'open_alerts':      Alert.objects.filter(is_resolved=False).count(),
        'critical_alerts':  Alert.objects.filter(is_resolved=False, severity='critical').count(),
        'banned_stations':  Station.objects.filter(is_banned=True).count(),
        'open_faults':      MechanicalFault.objects.filter(status='open').count(),
        'recent_alerts':    Alert.objects.filter(is_resolved=False, severity='critical').select_related('trip', 'trip__station').order_by('-created_at')[:6],
        'top_loss':         DischargeRecord.objects.filter(variance_liters__gt=0).select_related('trip', 'trip__station', 'agent').order_by('-variance_percent')[:8],
        'station_stats':    station_stats,
    }
    return render(request, 'dashboard/manager_dashboard.html', context)
@login_required
def station_stats(request):
    """متابعة المؤشرات الإحصائية لأداء المحطات (المدير العام)."""
    if request.user.role != 'manager':
        return redirect('dashboard:home')

    from django.db.models import Count, Sum, Avg, Q
    from trips.models import Station, DischargeRecord

    # مؤشرات كل محطة (تجميع من سجلات التفريغ عبر الرحلات)
    stations = Station.objects.annotate(
        discharge_count=Count('trip__discharge_record', distinct=True),
        total_volume=Sum('trip__discharge_record__discharge_volume_15c'),
        avg_variance=Avg('trip__discharge_record__variance_percent'),
        suspect_count=Count('trip__discharge_record',
                            filter=Q(trip__discharge_record__is_suspect=True), distinct=True),
    ).order_by('-discharge_count')

    # المحطة المختارة → بيانات المنحنى الزمني
    selected = None
    labels, variance_series, volume_series = [], [], []
    sid = request.GET.get('station')
    if sid:
        selected = Station.objects.filter(pk=sid).first()
        if selected:
            for r in DischargeRecord.objects.filter(trip__station=selected).order_by('created_at'):
                labels.append(r.created_at.strftime('%Y-%m-%d %H:%M'))
                variance_series.append(float(r.variance_percent))
                volume_series.append(float(r.discharge_volume_15c))

    context = {
        'stations': stations,
        'selected': selected,
        'record_count': len(labels),
        'labels_json':   json.dumps(labels, ensure_ascii=False),
        'variance_json': json.dumps(variance_series),
        'volume_json':   json.dumps(volume_series),
    }
    return render(request, 'dashboard/station_stats.html', context)
@login_required
def warehouse_stats(request):
    """متابعة المؤشرات الإحصائية لأداء المستودعات (المدير العام)."""
    if request.user.role != 'manager':
        return redirect('dashboard:home')

    from django.db.models import Count, Sum, Avg, Q
    from trips.models import Warehouse, DischargeRecord

    # مؤشرات كل مستودع (تجميع من الرحلات المنطلقة منه)
    warehouses = Warehouse.objects.annotate(
        trip_count=Count('trip', distinct=True),
        total_shipped=Sum('trip__shipped_volume_15c'),
        avg_variance=Avg('trip__discharge_record__variance_percent'),
        suspect_count=Count('trip__discharge_record',
                            filter=Q(trip__discharge_record__is_suspect=True), distinct=True),
    ).order_by('-trip_count')

    # المستودع المختار → المنحنى الزمني
    selected = None
    labels, variance_series, volume_series = [], [], []
    wid = request.GET.get('warehouse')
    if wid:
        selected = Warehouse.objects.filter(pk=wid).first()
        if selected:
            for r in DischargeRecord.objects.filter(trip__warehouse=selected).order_by('created_at'):
                labels.append(r.created_at.strftime('%Y-%m-%d %H:%M'))
                variance_series.append(float(r.variance_percent))
                volume_series.append(float(r.discharge_volume_15c))

    context = {
        'warehouses': warehouses,
        'selected': selected,
        'record_count': len(labels),
        'labels_json':   json.dumps(labels, ensure_ascii=False),
        'variance_json': json.dumps(variance_series),
        'volume_json':   json.dumps(volume_series),
    }
    return render(request, 'dashboard/warehouse_stats.html', context)

@login_required
def critical_alerts(request):
    """نافذة التنبيهات الحرجة للمدير العام (إدارة الأزمات)."""
    if request.user.role != 'manager':
        return redirect('dashboard:home')
    from alerts.models import Alert
    alerts = (Alert.objects.filter(severity='critical', is_resolved=False)
              .select_related('trip', 'trip__station').order_by('-created_at'))
    return render(request, 'dashboard/critical_alerts.html', {'alerts': alerts})


@login_required
@require_http_methods(["POST"])
def critical_alert_action(request, pk):
    """اتخاذ قرار إداري حاسم على تنبيه حرج + توثيقه."""
    if request.user.role != 'manager':
        return redirect('dashboard:home')
    from alerts.models import Alert
    from audit.models import AuditLog

    alert = get_object_or_404(Alert, pk=pk, severity='critical', is_resolved=False)
    decision = request.POST.get('decision', '')
    note = request.POST.get('note', '').strip()
    ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0] or request.META.get('REMOTE_ADDR', '')

    if decision == 'stop_station':
        st = alert.trip.station
        st.is_banned = True
        st.save(update_fields=['is_banned'])
        label = f'إيقاف المحطة «{st.station_name}»'
    elif decision == 'maintenance':
        label = 'إحالة لصيانة طارئة'
    elif decision == 'approve':
        label = 'اعتماد ومعالجة إدارية'
    else:
        messages.error(request, 'قرار غير صالح.')
        return redirect('dashboard:critical_alerts')

    # توثيق القرار وإغلاق التنبيه
    alert.is_resolved      = True
    alert.resolution_notes = f'قرار المدير العام: {label}.' + (f' | ملاحظة: {note}' if note else '')
    alert.resolved_by      = request.user
    alert.resolved_at      = timezone.now()
    alert.save()

    AuditLog.objects.create(
        user=request.user, action=f'manager_decision_{decision}',
        target_table='shield_alerts', target_id=alert.id,
        new_value=alert.resolution_notes, ip_address=ip,
    )
    messages.success(request, f'✅ تم اتخاذ القرار: {label} وتوثيقه في السجل.')
    return redirect('dashboard:critical_alerts')