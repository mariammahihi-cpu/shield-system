from django.urls import path
from . import views

app_name = 'alerts'

urlpatterns = [
    path('', views.alert_list, name='alert_list'),
    path('<int:pk>/', views.alert_detail, name='alert_detail'),
    path('<int:pk>/resolve/', views.resolve_alert, name='resolve_alert'),
    path('<int:alert_pk>/correction/', views.submit_correction_request, name='submit_correction_request'),
    path('correction/<int:pk>/review/', views.review_correction_request, name='review_correction_request'),
    path('notifications/', views.notifications, name='notifications'),
    path('trip/<int:trip_id>/request-correction/', views.request_thermal_correction, name='request_thermal_correction'),
]