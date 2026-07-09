from django.shortcuts import redirect
from django.contrib import auth
from django.urls import reverse

class BlockUnverifiedSessionsMiddleware:
    """
    وسيط برمجي (Middleware) يمنع المتصفحات والأجهزة التي تم إلغاء ثقتها 
    أو تسجيل الخروج منها من الوصول إلى صفحات المنظومة، ويطردها فوراً.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # التحقق يتم فقط إذا كان المستخدم مسجلاً دخوله بالفعل
        if request.user.is_authenticated:
            # جلب معرف الجلسة الموثوقة المخزن في الـ Session الحالية
            current_session_id = request.session.get('_verified_browser_session_id')
            
            if current_session_id:
                # استيراد الموديل ديناميكياً لتجنب مشاكل التداخل (Circular Import)
                from users.models import UserBrowserSession
                
                # التحقق من وجود الجلسة في قاعدة البيانات وأنها ما زالت موثوقة (is_trusted=True)
                session_exists = UserBrowserSession.objects.filter(
                    id=current_session_id, 
                    user=request.user, 
                    is_trusted=True
                ).exists()
                
                if not session_exists:
                    # إذا تم إلغاء الثقة بالجهاز من صفحة البروفايل، يتم طرده فوراً
                    auth.logout(request)
                    return redirect(reverse('users:login'))
            else:
                # حماية إضافية: إذا حاول الدخول بدون جلسة متصفح معلّمة أصلاً
                auth.logout(request)
                return redirect(reverse('users:login'))

        response = self.get_response(request)
        return response