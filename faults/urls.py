from django.urls import path
from . import views

app_name = 'faults'

urlpatterns = [
    # المسار التجريبي - لاختبار الربط
    path('', views.fault_list, name='list'),
    
    # مسارات إضافية (جاهزة للإضافة لاحقاً)
    # path('create/', views.create_fault, name='create'),
    # path('<int:pk>/', views.fault_detail, name='detail'),
    # path('<int:pk>/resolve/', views.resolve_fault, name='resolve'),
]