"""
Signal: send approval email when a LeaveRequest is created with status=pending.
Email errors are caught silently so they never crash the leave request submission.
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

logger = logging.getLogger(__name__)


@receiver(post_save, sender='leave.LeaveRequest')
def leave_request_created(sender, instance, created, **kwargs):
    if not created or instance.status != 'pending':
        return

    try:
        from hrms.email_utils import build_approval_urls, send_approval_email

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
    except Exception as exc:
        logger.error("leave_request_created signal failed: %s", exc, exc_info=True)


def _get_recipients(employee) -> list[str]:
    """Return list of email addresses to notify for an employee's request."""
    from accounts.models import User
    emails = []

    try:
        profile = employee.employee_profile
        if profile.direct_manager and profile.direct_manager.user:
            mgr_email = profile.direct_manager.user.email
            if mgr_email:
                emails.append(mgr_email)
    except Exception:
        pass

    if not emails:
        admin_emails = list(
            User.objects.filter(role='admin', email__isnull=False)
            .exclude(email='')
            .values_list('email', flat=True)
        )
        emails.extend(admin_emails)

    return emails
