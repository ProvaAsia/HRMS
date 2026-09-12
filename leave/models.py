from django.db import models
from django.conf import settings
from datetime import date, timedelta


class LeaveType(models.Model):
    name = models.CharField(max_length=100)
    name_th = models.CharField(max_length=100, blank=True)
    # Keep days_per_year for backward compat; new field is default_days
    days_per_year = models.PositiveIntegerField(default=0)
    default_days = models.IntegerField(default=0)
    annual_accrual = models.IntegerField(default=0, help_text="Extra days per year of service")
    requires_advance_days = models.IntegerField(default=0, help_text="Business days in advance required")
    is_paid = models.BooleanField(default=True)
    is_lwp = models.BooleanField(default=False, help_text="ลาไม่รับค่าจ้าง (Leave Without Pay) — ใช้เป็น fallback เมื่อวันลาหมด")
    carry_over = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class LeaveBalance(models.Model):
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leave_balances'
    )
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    year = models.IntegerField(default=2026)
    entitled_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    used_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)

    class Meta:
        unique_together = ['employee', 'leave_type', 'year']

    @property
    def remaining_days(self):
        return self.entitled_days - self.used_days

    # backward-compat alias
    @property
    def remaining(self):
        return self.remaining_days

    def __str__(self):
        return f"{self.employee} - {self.leave_type} {self.year}"


class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'รอการอนุมัติ'),
        ('approved', 'อนุมัติแล้ว'),
        ('rejected', 'ไม่อนุมัติ'),
        ('cancelled', 'ยกเลิก'),
    ]

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leave_requests'
    )
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    days = models.DecimalField(max_digits=4, decimal_places=1)
    reason = models.TextField(blank=True)
    medical_certificate = models.FileField(
        upload_to='medical_certs/%Y/%m/',
        null=True, blank=True,
        help_text="ใบรับรองแพทย์ — บังคับสำหรับลาป่วยเกิน 3 วัน"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # New fields
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='approved_leaves'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    # Keep old fields for backward compat
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reviewed_leaves'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.start_date})"

    def business_days_until_start(self):
        """Calculate business days from today to start_date."""
        today = date.today()
        if self.start_date <= today:
            return 0
        count = 0
        current = today + timedelta(days=1)
        while current <= self.start_date:
            if current.weekday() < 5:  # Mon-Fri
                count += 1
            current += timedelta(days=1)
        return count
