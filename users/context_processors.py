from .models import UserBrowserSession

def admin_pending_devices(request):
    """عدد الأجهزة غير الموثوقة المنتظرة اعتماد المدير."""
    if not request.user.is_authenticated:
        return {}
    if getattr(request.user, 'role', None) != 'admin':
        return {}
    count = UserBrowserSession.objects.filter(is_trusted=False).count()
    return {'pending_devices_count': count}
def admin_audit_badge(request):
    """عدد الإجراءات الإدارية الجديدة منذ آخر اطّلاع (للمدير)."""
    if not request.user.is_authenticated:
        return {}
    if getattr(request.user, 'role', None) != 'admin':
        return {}
    from audit.models import AdminAction
    qs = AdminAction.objects.all()
    if request.user.audit_seen_at:
        qs = qs.filter(created_at__gt=request.user.audit_seen_at)
    return {'new_audit_count': qs.count()}