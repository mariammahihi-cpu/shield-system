from django.urls import path
from . import views

app_name = 'audit'

urlpatterns = [
    # المسار التجريبي - لاختبار الربط
    path('', views.audit_log_list, name='list'),
    
    # مسارات إضافية (جاهزة للإضافة لاحقاً)
    # path('logs/<int:pk>/', views.audit_log_detail, name='log_detail'),
    # path('actions/', views.admin_action_list, name='actions'),
]