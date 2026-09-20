from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('employee', 'Employee'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    position = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == 'admin'

    # ── backward-compat aliases (templates & views ยังใช้ชื่อเดิมได้) ──
    @property
    def is_super_admin(self):
        return self.role == 'admin'

    @property
    def is_hr_manager(self):
        return False  # role นี้ถูกลบออกแล้ว

    @property
    def is_manager(self):
        return self.role == 'manager'

    @property
    def is_hr_or_admin(self):
        """เดิมใช้ตรวจ hr_manager | super_admin — ตอนนี้ตรงกับ admin เท่านั้น"""
        return self.role == 'admin'

    @property
    def can_approve(self):
        """Admin และ Manager อนุมัติ leave/OT ได้"""
        return self.role in ('admin', 'manager')

    def get_direct_report_users(self):
        """Return queryset of User objects who report directly to this user."""
        try:
            profile = self.employee_profile
            return type(self).objects.filter(
                employee_profile__direct_manager=profile
            )
        except Exception:
            return type(self).objects.none()

    def is_manager_of(self, employee_user):
        """Check if this user is the direct manager of another user."""
        try:
            emp_profile = employee_user.employee_profile
            return (
                emp_profile.direct_manager is not None
                and emp_profile.direct_manager.user_id == self.pk
            )
        except Exception:
            return False

    @property
    def initials(self):
        parts = self.get_full_name().split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        return self.username[:2].upper()

    @property
    def is_locked(self):
        """True if the account is currently locked due to too many failed logins."""
        return LoginAttempt.is_account_locked(self.username)

    def unlock(self):
        """Clear failed login attempts so the account becomes accessible again."""
        LoginAttempt.objects.filter(username=self.username, success=False).delete()


class LoginAttempt(models.Model):
    """Record each login attempt; 5 consecutive failures → account locked."""
    username = models.CharField(max_length=150, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    attempt_time = models.DateTimeField(default=timezone.now, db_index=True)
    success = models.BooleanField(default=False)

    MAX_FAILURES = 5

    class Meta:
        ordering = ['-attempt_time']

    def __str__(self):
        status = 'OK' if self.success else 'FAIL'
        return f"{self.username} [{status}] @ {self.attempt_time:%Y-%m-%d %H:%M}"

    @classmethod
    def is_account_locked(cls, username: str) -> bool:
        """Return True if the last MAX_FAILURES attempts are all failures (no success in between)."""
        recent = cls.objects.filter(username=username).order_by('-attempt_time')[:cls.MAX_FAILURES]
        recent = list(recent)
        if len(recent) < cls.MAX_FAILURES:
            return False
        return all(not a.success for a in recent)

    @classmethod
    def consecutive_failures(cls, username: str) -> int:
        """Count consecutive failures from the most recent attempt (stops at first success)."""
        count = 0
        for attempt in cls.objects.filter(username=username).order_by('-attempt_time')[:cls.MAX_FAILURES]:
            if attempt.success:
                break
            count += 1
        return count
