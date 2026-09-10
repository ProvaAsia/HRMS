from django.contrib import admin
from .models import LeaveType, LeaveBalance, LeaveRequest

admin.site.register(LeaveType)
admin.site.register(LeaveBalance)

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'start_date', 'end_date', 'days', 'status']
    list_filter = ['status', 'leave_type']
