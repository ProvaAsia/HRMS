"""
Signal: send approval email when an OTRequest is created with status=pending.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings


@receiver(post_save, sender='overtime.OTRequest')
def ot_request_created(sender, instance, created, **kwargs):
    if not created or instance.status != 'pending':
        return

    try:

        from hrms.email_utils import build_approval_urls, send_approval_email
        from accounts.models import User

        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        approve_url, reject_url = build_approval_urls(instance, 'ot', site_url)

        employee = instance.employee
        name = employee.get_full_name() or employee.username

        detail_lines = [
            f"พนักงาน: {name}",
            f"วันที่ OT: {instance.date}",
            f"เวลา: {instance.start_time:%H:%M} – {instance.end_time:%H:%M} ({instance.hours} ชั่วโมง)",
            f"เหตุผล: {instance.reason}",
        ]

        recipients = _get_recipients(employee)
        for to_email in recipients:
            send_approval_email(
                to_email=to_email,
                subject=f"[HRMS] คำขอทำ OT — {name}",
                requester_name=name,
                request_type="OT",
                detail_lines=detail_lines,
                approve_url=approve_url,
                reject_url=reject_url,
            )


    except Exception as exc:
        import logging
        logging.getLogger(__name__).error("signal failed: %s", exc, exc_info=True)

def _get_recipients(employee) -> list[str]:
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
