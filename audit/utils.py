from .models import AdminAction, AuditLog


def get_client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR')


def record_audit(request, action, target_table, target_id=None, old=None, new=None):
    """تسجيل تغيير عام (إنشاء/تعديل/تفعيل...) في AuditLog."""
    return AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        target_table=target_table,
        target_id=target_id,
        ip_address=get_client_ip(request),
        old_value=str(old) if old is not None else None,
        new_value=str(new) if new is not None else None,
    )


def record_admin_action(request, target_user, action_type, reason):
    """تسجيل إجراء إداري حسّاس (حظر/تجميد/فك قفل) مع مبرّر إلزامي."""
    return AdminAction.objects.create(
        target_user=target_user,
        admin_user=request.user,
        action_type=action_type,
        reason=reason,
    )