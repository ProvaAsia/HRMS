from django.contrib import admin
from .models import JobPosition, Candidate, Interview

@admin.register(JobPosition)
class JobPositionAdmin(admin.ModelAdmin):
    list_display = ['title', 'department', 'status', 'vacancies', 'deadline', 'created_at']
    list_filter = ['status', 'department']

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'job_position', 'status', 'applied_at']
    list_filter = ['status', 'job_position']

@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'interviewer', 'scheduled_at', 'result']
