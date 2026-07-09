def role_base_template(request):
    """
    يحقن متغيّر base_template في كل القوالب تلقائياً حسب دور المستخدم الحالي،
    بحيث تستطيع أي صفحة أن ترث الشريط الجانبي الصحيح عبر:
        {% extends base_template|default:'admin_base.html' %}
    """
    mapping = {
        'dispatcher': 'dispatcher_base.html',
        'agent':      'agent_base.html',
        'admin':      'admin_base.html',
        'manager':    'manager_base.html',
        'auditor':    'auditor_base.html',
    }
    user = getattr(request, 'user', None)
    role = getattr(user, 'role', None) if user and user.is_authenticated else None
    return {'base_template': mapping.get(role, 'admin_base.html')}