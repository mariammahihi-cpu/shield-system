from django.urls import path
from . import views

app_name = 'trips'

urlpatterns = [
    # المسار التجريبي - لاختبار الربط
    path('', views.trip_list, name='list'),
    
    # مسارات إضافية (جاهزة للإضافة لاحقاً)
    # path('create/', views.create_trip, name='create'),
    # path('<int:pk>/', views.trip_detail, name='detail'),
    # path('<int:pk>/discharge/', views.submit_discharge, name='discharge'),
    # path('<int:pk>/status/', views.update_trip_status, name='update_status'),
]