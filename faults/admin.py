from django.contrib import admin
from .models import MechanicalFault


@admin.register(MechanicalFault)
class MechanicalFaultAdmin(admin.ModelAdmin):
    list_display = ('id', 'fault_type', 'trip', 'station', 'truck', 'reported_by', 'is_critical', 'status', 'created_at')
    list_filter = ('fault_type', 'status', 'is_critical', 'created_at')
    search_fields = ('description', 'action_taken', 'reported_by__full_name', 'trip__trip_code', 'station__station_name')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)