from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('login/',             views.login_view,       name='login'),
    path('logout/',            views.logout_view,      name='logout'),
    path('users/',             views.user_list,        name='user_list'),
    path('users/create/',      views.create_user,      name='create_user'),
    path('users/<int:user_id>/toggle-lock/', views.toggle_lock_user, name='toggle_lock'),
]