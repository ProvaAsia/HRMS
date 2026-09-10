from django.contrib import admin
from .models import AppraisalCycle, Appraisal, Goal

@admin.register(AppraisalCycle)
class AppraisalCycleAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'status']

@admin.register(Appraisal)
class AppraisalAdmin(admin.ModelAdmin):
    list_display = ['employee', 'cycle', 'manager', 'status', 'self_rating', 'manager_rating']
    list_filter = ['status', 'cycle']

@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ['title', 'appraisal', 'status', 'weight', 'achievement']
