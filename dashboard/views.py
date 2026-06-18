from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta


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
    from trips.models import Trip, Station, DischargeRecord
    from alerts.models import Alert
    from users.models import User
    now = timezone.now()
    total_variance = DischargeRecord.objects.aggregate(total=Sum('volume_variance'))['total'] or 0
    context = {
        'total_trips':     Trip.objects.count(),
        'completed_trips': Trip.objects.filter(status='completed').count(),
        'total_variance':  round(float(total_variance), 2),
        'banned_stations': Station.objects.filter(is_banned=True).count(),
        'open_alerts':     Alert.objects.filter(is_resolved=False).count(),
        'trips_by_status': Trip.objects.values('status').annotate(count=Count('id')),
        'alerts_by_type':  Alert.objects.values('alert_type').annotate(count=Count('id')),
        'recent_alerts':   Alert.objects.filter(is_resolved=False, severity='critical').order_by('-created_at')[:5],
        'top_loss_trips':  DischargeRecord.objects.filter(variance_percent__gt=0.5).order_by('-variance_percent')[:10],
        'total_users':     User.objects.count(),
    }
    return render(request, 'dashboard/manager_dashboard.html', context)