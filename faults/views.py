from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.urls import reverse

from users.decorators import role_required, get_client_ip
from audit.models import AuditLog
from .models import MechanicalFault


@login_required
@role_required('auditor', 'manager', 'admin')
def fault_list(request):
    faults = (
        MechanicalFault.objects
        .select_related('reported_by', 'trip', 'station', 'truck')
        .order_by('-created_at')
    )
    return render(request, 'faults/fault_list.html', {'faults': faults})


@login_required
@role_required('auditor', 'manager', 'admin')
def fault_detail(request, pk):
    """صفحة تفاصيل بلاغ واحد بكامل بياناته وإجراءات المعالجة."""
    fault = get_object_or_404(
        MechanicalFault.objects.select_related('reported_by', 'trip', 'station', 'truck'),
        pk=pk,
    )
    return render(request, 'faults/fault_detail.html', {'fault': fault})


@login_required
@require_http_methods(["POST"])
@role_required('auditor', 'manager', 'admin')
def resolve_fault(request, pk):
    """معالجة بلاغ: بدء الإصلاح أو الإغلاق بملاحظة، مع توثيق القرار في سجل التدقيق."""
    fault = get_object_or_404(MechanicalFault, pk=pk)

    # الرجوع لنفس الصفحة التي انطلق منها الإجراء (القائمة أو التفاصيل)
    next_url = request.POST.get('next')
    if not (next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()})):
        next_url = reverse('faults:list')

    action = request.POST.get('action')
    old_status = fault.status

    if action == 'start':
        if fault.status != 'open':
            messages.error(request, 'لا يمكن بدء المعالجة إلا لبلاغ مفتوح.')
            return redirect(next_url)
        fault.status = 'fixing'
        fault.save(update_fields=['status'])
        log_action = 'fault_start_fixing'
        messages.success(request, '🔧 تم بدء معالجة البلاغ.')

    elif action == 'close':
        if fault.status == 'closed':
            messages.error(request, 'البلاغ مغلق بالفعل.')
            return redirect(next_url)
        note = (request.POST.get('action_taken') or '').strip()
        if not note:
            messages.error(request, 'يجب إدخال ملاحظة الإصلاح قبل الإغلاق.')
            return redirect(next_url)
        fault.status = 'closed'
        fault.action_taken = note
        fault.resolved_at = timezone.now()
        fault.save(update_fields=['status', 'action_taken', 'resolved_at'])
        log_action = 'fault_close'
        messages.success(request, '✅ تم إغلاق البلاغ وتوثيق الإجراء.')

    else:
        messages.error(request, 'إجراء غير معروف.')
        return redirect(next_url)

    AuditLog.objects.create(
        user=request.user, action=log_action,
        target_table='shield_mechanical_faults', target_id=fault.id,
        old_value=old_status, new_value=fault.status,
        ip_address=get_client_ip(request),
    )
    return redirect(next_url)