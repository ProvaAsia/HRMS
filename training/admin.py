from django.contrib import admin
from .models import TrainingProgram, TrainingEnrollment

@admin.register(TrainingProgram)
class TrainingProgramAdmin(admin.ModelAdmin):
    list_display = ['title', 'trainer', 'start_date', 'end_date', 'status', 'max_participants']
    list_filter = ['status', 'category']

@admin.register(TrainingEnrollment)
class TrainingEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'training', 'status', 'enrolled_at']
    list_filter = ['status']
