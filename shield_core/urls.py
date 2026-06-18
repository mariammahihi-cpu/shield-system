from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls', namespace='users')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('trips/', include('trips.urls', namespace='trips')),
    path('alerts/', include('alerts.urls', namespace='alerts')),
    path('faults/', include('faults.urls', namespace='faults')),
    path('audit/', include('audit.urls', namespace='audit')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)