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
    path('manager/', views.manager_dashboard, name='manager'),
]