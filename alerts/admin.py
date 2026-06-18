from django.contrib import admin
from .models import Alert, CorrectionRequest


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('id', 'trip', 'alert_type', 'severity', 'is_resolved', 'created_at', 'resolved_by')
    list_filter = ('severity', 'alert_type', 'is_resolved')
    search_fields = ('trip__trip_code', 'description')
    readonly_fields = ('trip', 'alert_type', 'severity', 'description', 'created_at')
    ordering = ('-created_at',)


@admin.register(CorrectionRequest)
class CorrectionRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'alert', 'requested_by', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('alert__trip__trip_code', 'reason')
    readonly_fields = ('alert', 'requested_by', 'created_at')
    ordering = ('-created_at',)