from django.urls import path
from . import views

app_name = 'faults'

urlpatterns = [
    # المسار التجريبي - لاختبار الربط
    path('', views.fault_list, name='list'),
    path('<int:pk>/resolve/', views.resolve_fault, name='resolve'),
    path('<int:pk>/', views.fault_detail, name='detail'),
]