from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', views.admin_dashboard, name='admin'),
    path('dispatcher/', views.dispatcher_dashboard, name='dispatcher'),
    path('driver/', views.driver_dashboard, name='driver'),
    path('agent/', views.agent_dashboard, name='agent'),
    path('auditor/', views.auditor_dashboard, name='auditor'),
    path('manager/', views.manager_dashboard, name='manager_dashboard'),
    path('manager/stations/', views.station_stats, name='station_stats'),
    path('manager/critical-alerts/',  views.critical_alerts, name='critical_alerts'),
    path('manager/critical-alerts/<int:pk>/decide/', views.critical_alert_action, name='critical_alert_action'),
]