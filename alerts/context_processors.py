from .models import Alert

def notifications_badge(request):
    """عدد الإشعارات غير المقروءة — لأدوار الرقابة فقط (المراقب/المدير/الأدمن)."""
    if not request.user.is_authenticated:
        return {}

    role = getattr(request.user, 'role', None)
    # الإنذارات أداة رقابة → لا تُعرض للمندوب/موظف المستودع (المُراقَبين)
    if role not in ('auditor', 'manager', 'admin'):
        return {}

    qs = Alert.objects.all()
    if request.user.notifications_seen_at:
        qs = qs.filter(created_at__gt=request.user.notifications_seen_at)

    return {'unread_notifications': qs.count()}