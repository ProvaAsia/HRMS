from django.db import models
from django.conf import settings


class AttendanceRecord(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('late', 'Late'),
        ('half_day', 'Half Day'),
        ('absent', 'Absent'),
        ('wfh', 'Work from Home'),
        ('leave', 'On Leave'),
    ]

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attendance_records'
    )
    date = models.DateField()
    clock_in = models.TimeField(null=True, blank=True)
    clock_out = models.TimeField(null=True, blank=True)
    work_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee.get_full_name()} — {self.date} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if self.clock_in and self.clock_out:
            from datetime import datetime, date
            ci = datetime.combine(date.today(), self.clock_in)
            co = datetime.combine(date.today(), self.clock_out)
            diff = co - ci
            if diff.total_seconds() > 0:
                self.work_hours = round(diff.total_seconds() / 3600, 2)
        super().save(*args, **kwargs)
