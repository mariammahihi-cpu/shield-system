from django.urls import path
from . import views

app_name = 'alerts'

urlpatterns = [
    # المسار التجريبي - لاختبار الربط
    path('', views.alert_list, name='list'),
    
    # مسارات إضافية (جاهزة للإضافة لاحقاً)
    # path('<int:pk>/', views.alert_detail, name='detail'),
    # path('<int:pk>/resolve/', views.resolve_alert, name='resolve'),
]