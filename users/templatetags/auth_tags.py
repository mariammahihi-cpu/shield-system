from django import template

register = template.Library()


@register.filter
def has_role(user, role):
    """
    فلتر لـ Django Templates للتحقق من دور المستخدم
    
    الاستخدام في HTML:
        {% if user|has_role:'admin' %}
            <button class="btn btn-danger">حذف</button>
        {% endif %}
    
    أو مع متعدد:
        {% if user|has_role:'admin,manager' %}
            <a href="{% url 'dashboard' %}">اللوحة</a>
        {% endif %}
    """
    if not user.is_authenticated:
        return False
    
    # إذا كان المدخل متعدد (مثل 'admin,manager')
    if ',' in role:
        allowed_roles = [r.strip() for r in role.split(',')]
        return user.role in allowed_roles
    
    # دور واحد فقط
    return user.role == role


@register.filter
def role_display(user):
    """
    فلتر لعرض اسم الدور بشكل مقروء
    
    الاستخدام:
        <span>{{ user|role_display }}</span>
        → يعرض: "مدير النظام" بدل "admin"
    """
    if not user.is_authenticated:
        return 'غير مسجل'
    return user.get_role_display()


@register.simple_tag
def user_can_edit(user, resource_type):
    """
    وسم لإرجاع True إذا كان المستخدم يستطيع تعديل المورد
    
    الاستخدام:
        {% user_can_edit user 'trip' as can_edit %}
        {% if can_edit %}
            <a href="edit">تعديل</a>
        {% endif %}
    """
    edit_permissions = {
        'trip': ['admin', 'manager', 'dispatcher'],
        'discharge': ['admin', 'manager', 'agent'],
        'truck': ['admin', 'manager'],
        'user': ['admin'],
    }
    
    allowed_roles = edit_permissions.get(resource_type, [])
    return user.is_authenticated and user.role in allowed_roles


@register.simple_tag
def user_full_info(user):
    """وسم لعرض معلومات المستخدم الكاملة"""
    if not user.is_authenticated:
        return 'زائر'
    return f'{user.full_name} ({user.get_role_display()})'