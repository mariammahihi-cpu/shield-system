from .models import MechanicalFault


def faults_badge(request):
    """عدّاد البلاغات المفتوحة — يظهر في الشريط الجانبي لكل القوالب."""
    if not request.user.is_authenticated:
        return {}

    role = getattr(request.user, 'role', None)

    # المراقب / المدير العام / المدير فقط من يرى العدّاد
    if role not in ('auditor', 'manager', 'admin'):
        return {}

    return {
        # كل البلاغات المفتوحة → للمراقب
        'open_faults_count':     MechanicalFault.objects.filter(status='open').count(),
        # البلاغات الحرجة المفتوحة → تصعيد للمدير العام
        'critical_faults_count': MechanicalFault.objects.filter(status='open', is_critical=True).count(),
    }