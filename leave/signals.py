"""
Signal: send approval email when a LeaveRequest is created with status=pending.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings


@receiver(post_save, sender='leave.LeaveRequest')
def leave_request_created(sender, instance, created, **kwargs):
    if not created or instance.status != 'pending':
        return

    from hrms.email_utils import build_approval_urls, send_approval_email
    from accounts.models import User

    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    approve_url, reject_url = build_approval_urls(instance, 'leave', site_url)

    employee = instance.employee
    name = employee.get_full_name() or employee.username

    detail_lines = [
        f"ผู้ขอลา: {name}",
        f"ประเภทการลา: {instance.leave_type.name}",
        f"วันที่: {instance.start_date} – {instance.end_date} ({instance.days} วัน)",
    ]
    if instance.reason:
        detail_lines.append(f"เหตุผล: {instance.reason}")

    # Find recipients: direct manager first, fall back to all admins
    recipients = _get_recipients(employee)
    for to_email in recipients:
        send_approval_email(
            to_email=to_email,
            subject=f"[HRMS] คำขอลา — {name}",
            requester_name=name,
            request_type="ลา",
            detail_lines=detail_lines,
            approve_url=approve_url,
            reject_url=reject_url,
        )


def _get_recipients(employee) -> list[str]:
    """Return list of email addresses to notify for an employee's request."""
    from accounts.models import User
    emails = []

    # Try direct manager via EmployeeProfile
    try:
        profile = employee.employee_profile
        if profile.direct_manager and profile.direct_manager.user:
            mgr_email = profile.direct_manager.user.email
            if mgr_email:
                emails.append(mgr_email)
    except Exception:
        pass

    # Fall back to all admins if no manager email found
    if not emails:
        admin_emails = list(
            User.objects.filter(role='admin', email__isnull=False)
            .exclude(email='')
            .values_list('email', flat=True)
        )
        emails.extend(admin_emails)

    return emails
