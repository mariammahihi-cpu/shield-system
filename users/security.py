from .models import UserBrowserSession

DEVICE_COOKIE = 'shield_browser_fp'

def get_bound_session(request):
    """جلسة الجهاز الموثوقة المطابقة لبصمة الكوكي، أو None."""
    fp = request.COOKIES.get(DEVICE_COOKIE)
    if not fp or not request.user.is_authenticated:
        return None
    return UserBrowserSession.objects.filter(
        user=request.user, browser_fingerprint=fp, is_trusted=True
    ).first()

def is_trusted_device(request):
    return get_bound_session(request) is not None