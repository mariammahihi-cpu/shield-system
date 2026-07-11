from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Alert, CorrectionRequest
from audit.models import AuditLog


def _get_ip(request):
    x_fwd = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_fwd.split(',')[0] if x_fwd else request.META.get('REMOTE_ADDR', '')


@login_required
def alert_list(request):
    if request.user.role not in ('auditor', 'manager', 'admin'):
        messages.error(request, 'ليس لديك صلاحية.')
        return redirect('dashboard:home')

    alerts = Alert.objects.select_related('trip', 'resolved_by').order_by('-created_at')

    severity_filter = request.GET.get('severity', '')
    type_filter     = request.GET.get('alert_type', '')
    resolved_filter = request.GET.get('resolved', '')

    if severity_filter:
        alerts = alerts.filter(severity=severity_filter)
    if type_filter:
        alerts = alerts.filter(alert_type=type_filter)
    if resolved_filter == 'yes':
        alerts = alerts.filter(is_resolved=True)
    elif resolved_filter == 'no':
        alerts = alerts.filter(is_resolved=False)

    return render(request, 'alerts/alert_list.html', {
        'alerts': alerts,
        'severity_choices': Alert.SEVERITY_LEVELS,
        'type_choices': Alert.ALERT_TYPES,
        'severity_filter': severity_filter,
        'type_filter': type_filter,
        'resolved_filter': resolved_filter,
        'open_count': Alert.objects.filter(is_resolved=False).count(),
        'critical_count': Alert.objects.filter(is_resolved=False, severity='critical').count(),
    })


@login_required
def alert_detail(request, pk):
    if request.user.role not in ('auditor', 'manager', 'admin'):
        messages.error(request, 'ليس لديك صلاحية.')
        return redirect('dashboard:home')

    alert = get_object_or_404(
        Alert.objects.select_related(
            'trip__station', 'trip__truck', 'trip__truck__driver', 'trip__discharge_record'
        ),
        pk=pk
    )
    correction_requests = alert.correction_requests.select_related('requested_by').order_by('-created_at')

    return render(request, 'alerts/alert_detail.html', {
        'alert': alert,
        'correction_requests': correction_requests,
    })


@login_required
def resolve_alert(request, pk):
    if request.user.role not in ('auditor', 'admin'):
        messages.error(request, 'ليس لديك صلاحية.')
        return redirect('dashboard:home')

    alert = get_object_or_404(Alert, pk=pk, is_resolved=False)

    if request.method == 'POST':
        notes = request.POST.get('resolution_notes', '').strip()
        if not notes:
            messages.error(request, 'يجب إدخال ملاحظات القرار.')
            return redirect('alerts:alert_detail', pk=pk)

        alert.is_resolved      = True
        alert.resolution_notes = notes
        alert.resolved_by      = request.user
        alert.resolved_at      = timezone.now()
        alert.save()

        AuditLog.objects.create(
            user=request.user, action='resolve_alert',
            target_table='shield_alerts', target_id=alert.id,
            new_value=notes, ip_address=_get_ip(request),
        )
        messages.success(request, 'تم إغلاق الإنذار بنجاح.')
        return redirect('alerts:alert_list')

    return redirect('alerts:alert_detail', pk=pk)


@login_required
def submit_correction_request(request, alert_pk):
    if request.user.role not in ('agent', 'dispatcher'):
        messages.error(request, 'ليس لديك صلاحية.')
        return redirect('dashboard:home')

    alert = get_object_or_404(Alert, pk=alert_pk, is_resolved=False)

    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        if not reason:
            messages.error(request, 'يجب إدخال سبب طلب التصحيح.')
            return redirect('alerts:alert_detail', pk=alert_pk)

        CorrectionRequest.objects.create(
            alert=alert,
            requested_by=request.user,
            reason=reason,
        )
        AuditLog.objects.create(
            user=request.user, action='submit_correction_request',
            target_table='shield_alerts', target_id=alert.id,
            new_value=reason, ip_address=_get_ip(request),
        )
        messages.success(request, 'تم إرسال طلب التصحيح بنجاح.')
        return redirect('alerts:alert_detail', pk=alert_pk)

    return redirect('alerts:alert_detail', pk=alert_pk)


@login_required
def review_correction_request(request, pk):
    if request.user.role != 'auditor':
        messages.error(request, 'ليس لديك صلاحية.')
        return redirect('dashboard:home')

    correction = get_object_or_404(CorrectionRequest, pk=pk, status='pending')

    if request.method == 'POST':
        decision = request.POST.get('decision')
        notes    = request.POST.get('notes', '').strip()

        if decision not in ('approved', 'rejected'):
            messages.error(request, 'قرار غير صالح.')
            return redirect('alerts:alert_detail', pk=correction.alert.pk)

        correction.status      = decision
        correction.reviewed_by = request.user
        correction.review_notes = notes
        correction.reviewed_at = timezone.now()
        correction.save()

        AuditLog.objects.create(
            user=request.user, action=f'correction_{decision}',
            target_table='shield_alerts', target_id=correction.alert.id,
            new_value=notes, ip_address=_get_ip(request),
        )
        status_msg = 'قبول' if decision == 'approved' else 'رفض'
        messages.success(request, f'تم {status_msg} طلب التصحيح.')
        return redirect('alerts:alert_detail', pk=correction.alert.pk)

    return redirect('alerts:alert_detail', pk=correction.alert.pk)
#الاشعارات 
@login_required
def notifications(request):
    """عرض الإشعارات لأدوار الرقابة فقط، وتعليمها كمقروءة عند الفتح."""
    if request.user.role not in ('auditor', 'manager', 'admin'):
        messages.error(request, 'ليس لديك صلاحية.')
        return redirect('dashboard:home')

    qs = Alert.objects.select_related('trip').order_by('-created_at')
    alerts = list(qs)   # نجلبها قبل تحديث وقت الاطّلاع

    request.user.notifications_seen_at = timezone.now()
    request.user.save(update_fields=['notifications_seen_at'])

    return render(request, 'alerts/notifications.html', {'alerts': alerts})
@login_required
def request_thermal_correction(request, trip_id):
    """المندوب/الموظف يقدّم طلب تصحيح حراري على رحلة مشبوهة."""
    from trips.models import Trip
    if request.user.role not in ('agent', 'dispatcher'):
        messages.error(request, 'ليس لديك صلاحية.')
        return redirect('dashboard:home')
    if request.method != 'POST':
        return redirect('trips:discharge_log')

    trip = get_object_or_404(Trip, pk=trip_id)
    if request.user.role == 'agent' and trip.agent != request.user:
        messages.error(request, 'غير مصرح: هذه الرحلة ليست من توثيقك.')
        return redirect('trips:discharge_log')

    reason = request.POST.get('reason', '').strip()
    if not reason:
        messages.error(request, 'يجب إدخال سبب طلب التصحيح الحراري.')
        return redirect('trips:discharge_log')

    # إيجاد إنذار مفتوح للرحلة أو إنشاؤه (لربط الطلب به)
    alert = Alert.objects.filter(trip=trip, is_resolved=False).first()
    if not alert:
        alert = Alert.objects.create(
            trip=trip, alert_type='volume_variance', severity='medium',
            description=f'طلب تصحيح حراري من المندوب على الرحلة {trip.trip_code}.',
        )

    # منع طلب مكرّر معلّق
    if CorrectionRequest.objects.filter(alert=alert, status='pending').exists():
        messages.warning(request, 'يوجد طلب تصحيح معلّق بالفعل لهذه الرحلة.')
        return redirect('trips:discharge_log')

    CorrectionRequest.objects.create(alert=alert, requested_by=request.user, reason=reason)
    AuditLog.objects.create(
        user=request.user, action='submit_correction_request',
        target_table='shield_alerts', target_id=alert.id,
        new_value=reason, ip_address=_get_ip(request),
    )
    messages.success(request, '✅ تم إرسال طلب التصحيح الحراري للمراجعة بنجاح.')
    return redirect('trips:discharge_log')