from django.contrib import admin
from .models import OTRequest


@admin.register(OTRequest)
class OTRequestAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'start_time', 'end_time', 'hours', 'status']
    list_filter = ['status', 'date']
