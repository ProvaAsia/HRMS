from django.contrib import admin
from .models import AttendanceRecord


@admin.register(AttendanceRecord)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'clock_in', 'clock_out', 'work_hours', 'status']
    list_filter = ['status', 'date']
    search_fields = ['employee__first_name', 'employee__last_name']
