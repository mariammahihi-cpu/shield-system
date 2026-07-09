from .models import Alert

def notifications_badge(request):
    """عدد الإشعارات غير المقروءة — يظهر في كل القوالب."""
    if not request.user.is_authenticated:
        return {}

    user = request.user
    role = getattr(user, 'role', None)
    qs = Alert.objects.all()

    if role == 'agent':
        qs = qs.filter(trip__agent=user)
    elif role == 'dispatcher':
        qs = qs.filter(trip__dispatcher=user)
    elif role not in ('manager', 'admin', 'auditor'):
        return {'unread_notifications': 0}

    if user.notifications_seen_at:
        qs = qs.filter(created_at__gt=user.notifications_seen_at)

    return {'unread_notifications': qs.count()}