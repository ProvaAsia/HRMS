from django.db import models
from django.utils import timezone
from accounts.models import User


class LeaveType(models.Model):
    name = models.CharField(max_length=100)
    days_per_year = models.PositiveIntegerField(default=0)
    is_paid = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class LeaveBalance(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    year = models.PositiveIntegerField(default=2026)
    entitled_days = models.DecimalField(max_digits=5, decimal_places=1)
    used_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)

    class Meta:
        unique_together = ('employee', 'leave_type', 'year')

    def __str__(self):
        return f"{self.employee.get_full_name()} — {self.leave_type} ({self.year})"

    @property
    def remaining(self):
        return self.entitled_days - self.used_days


class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    days = models.DecimalField(max_digits=4, decimal_places=1)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_leaves')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.get_full_name()} — {self.leave_type} {self.start_date}"
