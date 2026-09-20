"""
Signal: send approval email when a Candidate is created (status=applied).
Notifies HR/admin to review and advance or reject the candidate.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings


@receiver(post_save, sender='recruitment.Candidate')
def candidate_created(sender, instance, created, **kwargs):
    if not created or instance.status != 'applied':
        return

    try:

        from hrms.email_utils import build_approval_urls, send_approval_email
        from accounts.models import User

        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        approve_url, reject_url = build_approval_urls(instance, 'candidate', site_url)

        candidate_name = f"{instance.first_name} {instance.last_name}"
        detail_lines = [
            f"ผู้สมัคร: {candidate_name}",
            f"ตำแหน่ง: {instance.job_position.title}",
            f"แผนก: {instance.job_position.department}",
            f"อีเมล: {instance.email}",
        ]
        if instance.phone:
            detail_lines.append(f"โทรศัพท์: {instance.phone}")

        # Notify all admins
        recipients = list(
            User.objects.filter(role='admin', email__isnull=False)
            .exclude(email='')
            .values_list('email', flat=True)
        )
        for to_email in recipients:
            send_approval_email(
                to_email=to_email,
                subject=f"[HRMS] ผู้สมัครใหม่ — {candidate_name}",
                requester_name=candidate_name,
                request_type="สมัครงาน",
                detail_lines=detail_lines,
                approve_url=approve_url,
                reject_url=reject_url,
            )
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error("signal failed: %s", exc, exc_info=True)

