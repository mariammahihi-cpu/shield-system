from django.shortcuts import render
from .models import AuditLog

def audit_log_list(request):
    logs = AuditLog.objects.all()
    return render(request, 'audit/audit_log_list.html', {'logs': logs})