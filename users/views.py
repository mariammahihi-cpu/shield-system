from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import User, UserDevice
from audit.models import AuditLog


MAX_LOGIN_ATTEMPTS = 5


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        try:
            user_obj = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة.')
            return render(request, 'users/login.html')

        if user_obj.is_locked:
            messages.error(request, 'تم تجميد هذا الحساب. تواصل مع مدير النظام.')
            return render(request, 'users/login.html')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            user.login_attempts = 0
            user.save(update_fields=['login_attempts'])
            login(request, user)
            AuditLog.objects.create(
                user=user,
                action='login',
                target_table='shield_users',
                target_id=user.id,
                ip_address=get_client_ip(request),
            )
            return redirect('dashboard:home')
        else:
            user_obj.login_attempts += 1
            if user_obj.login_attempts >= MAX_LOGIN_ATTEMPTS:
                user_obj.is_locked = True
                messages.error(request, 'تم تجميد حسابك بسبب تكرار المحاولات الفاشلة.')
            else:
                remaining = MAX_LOGIN_ATTEMPTS - user_obj.login_attempts
                messages.error(request, f'كلمة المرور غير صحيحة. متبقي {remaining} محاولة.')
            user_obj.save(update_fields=['login_attempts', 'is_locked'])

    return render(request, 'users/login.html')


@login_required
def logout_view(request):
    AuditLog.objects.create(
        user=request.user,
        action='logout',
        target_table='shield_users',
        target_id=request.user.id,
        ip_address=get_client_ip(request),
    )
    logout(request)
    return redirect('users:login')


@login_required
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not authenticate(request, username=request.user.username, password=current_password):
            messages.error(request, 'كلمة المرور الحالية غير صحيحة.')
            return render(request, 'users/change_password.html')

        if new_password != confirm_password:
            messages.error(request, 'كلمات المرور الجديدة غير متطابقة.')
            return render(request, 'users/change_password.html')

        if len(new_password) < 8:
            messages.error(request, 'يجب أن تكون كلمة المرور 8 أحرف على الأقل.')
            return render(request, 'users/change_password.html')

        request.user.set_password(new_password)
        request.user.save()
        update_session_auth_hash(request, request.user)
        
        AuditLog.objects.create(
            user=request.user,
            action='change_password',
            target_table='shield_users',
            target_id=request.user.id,
            ip_address=get_client_ip(request),
        )
        messages.success(request, 'تم تغيير كلمة المرور بنجاح.')
        return redirect('dashboard:home')

    return render(request, 'users/change_password.html')


@login_required
def user_list(request):
    if request.user.role != 'admin':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة.')
        return redirect('dashboard:home')
    users = User.objects.all().order_by('role', 'full_name')
    return render(request, 'users/user_list.html', {'users': users})


@login_required
def create_user(request):
    if request.user.role != 'admin':
        messages.error(request, 'ليس لديك صلاحية.')
        return redirect('dashboard:home')

    if request.method == 'POST':
        username     = request.POST.get('username', '').strip()
        full_name    = request.POST.get('full_name', '').strip()
        role         = request.POST.get('role', '')
        phone_number = request.POST.get('phone_number', '').strip()
        password     = request.POST.get('password', '')

        if not all([username, full_name, role, password]):
            messages.error(request, 'جميع الحقول مطلوبة.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'اسم المستخدم موجود مسبقاً.')
        elif phone_number and User.objects.filter(phone_number=phone_number).exists():
            messages.error(request, 'رقم الهاتف موجود مسبقاً.')
        elif len(password) < 8:
            messages.error(request, 'يجب أن تكون كلمة المرور 8 أحرف على الأقل.')
        else:
            user = User.objects.create_user(
                username=username,
                full_name=full_name,
                role=role,
                phone_number=phone_number,
                password=password,
            )
            AuditLog.objects.create(
                user=request.user,
                action='create_user',
                target_table='shield_users',
                target_id=user.id,
                new_value=f'{username} ({role})',
                ip_address=get_client_ip(request),
            )
            messages.success(request, f'تم إنشاء حساب {full_name} بنجاح.')
            return redirect('users:user_list')

    roles = User.ROLE_CHOICES
    return render(request, 'users/create_user.html', {'roles': roles})


@login_required
def toggle_lock_user(request, user_id):
    if request.user.role != 'admin':
        messages.error(request, 'ليس لديك صلاحية.')
        return redirect('dashboard:home')

    target = get_object_or_404(User, pk=user_id)
    if target == request.user:
        messages.error(request, 'لا يمكنك تجميد حسابك الخاص.')
        return redirect('users:user_list')

    target.is_locked = not target.is_locked
    target.login_attempts = 0
    target.save(update_fields=['is_locked', 'login_attempts'])

    action = 'lock_user' if target.is_locked else 'unlock_user'
    AuditLog.objects.create(
        user=request.user,
        action=action,
        target_table='shield_users',
        target_id=target.id,
        ip_address=get_client_ip(request),
    )
    status_msg = 'تجميد' if target.is_locked else 'تفعيل'
    messages.success(request, f'تم {status_msg} حساب {target.full_name}.')
    return redirect('users:user_list')


def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0]
    return request.META.get('REMOTE_ADDR', '')