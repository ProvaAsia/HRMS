from django.contrib import admin
from .models import (
    Division, Department, CostCenter, WorkLocation,
    EmployeeProfile, EmergencyContact, Dependent
)


class EmergencyContactInline(admin.TabularInline):
    model = EmergencyContact
    extra = 1


class DependentInline(admin.TabularInline):
    model = Dependent
    extra = 1


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'full_name_en', 'department', 'job_title', 'employment_type', 'join_date']
    list_filter = ['department', 'division', 'employment_type', 'work_location']
    search_fields = ['employee_id', 'first_name_en', 'last_name_en', 'first_name_th', 'last_name_th']
    inlines = [EmergencyContactInline, DependentInline]


admin.site.register(Division)
admin.site.register(Department)
admin.site.register(CostCenter)
admin.site.register(WorkLocation)
