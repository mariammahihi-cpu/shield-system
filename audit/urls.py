from django.urls import path
from . import views

app_name = 'audit'

urlpatterns = [
    path('logs/',    views.audit_log_list,    name='audit_log_list'),
    path('actions/', views.admin_action_list, name='admin_action_list'),
]
from django.urls import path
from . import views

app_name = 'audit'

urlpatterns = [
    path('',        views.audit_log_list,    name='list'),
    path('actions/', views.admin_action_list, name='actions'),
]