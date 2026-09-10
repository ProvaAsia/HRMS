from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('hr_manager', 'HR Manager'),
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
    def is_super_admin(self):
        return self.role == 'super_admin'

    @property
    def is_hr_manager(self):
        return self.role == 'hr_manager'

    @property
    def is_manager(self):
        return self.role == 'manager'

    @property
    def is_hr_or_admin(self):
        return self.role in ('super_admin', 'hr_manager')

    @property
    def can_approve(self):
        """True if this user can approve leave/OT (manager, hr_manager, or super_admin)."""
        return self.role in ('super_admin', 'hr_manager', 'manager')

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
