"""
Helpers for sending approval/rejection emails with signed tokens.

Token format (signed with TimestampSigner):
  <model_type>:<pk>:<action>
  e.g.  leave:42:approve  or  ot:7:reject

Tokens expire after APPROVAL_TOKEN_MAX_AGE_HOURS hours (default 72).
"""
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

APPROVAL_TOKEN_MAX_AGE_HOURS = 72  # 3 days

_signer = TimestampSigner(salt='hrms-approval')


# ── Token helpers ────────────────────────────────────────────────────────────

def make_approval_token(model_type: str, pk: int, action: str) -> str:
    """Return a URL-safe signed token string."""
    value = f"{model_type}:{pk}:{action}"
    return _signer.sign(value)


def parse_approval_token(token: str):
    """
    Verify and decode a token.
    Returns (model_type, pk, action) on success.
    Raises BadSignature or SignatureExpired on failure.
    """
    max_age = APPROVAL_TOKEN_MAX_AGE_HOURS * 3600
    value = _signer.unsign(token, max_age=max_age)
    model_type, pk_str, action = value.rsplit(':', 2)
    return model_type, int(pk_str), action


# ── Email sender ─────────────────────────────────────────────────────────────

def send_approval_email(*, to_email: str, subject: str, requester_name: str,
                        request_type: str, detail_lines: list[str],
                        approve_url: str, reject_url: str) -> bool:
    """
    Render the approval email template and send it.
    Returns True on success, False on failure.
    """
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    html_body = render_to_string('emails/approval_email.html', {
        'requester_name': requester_name,
        'request_type': request_type,
        'detail_lines': detail_lines,
        'approve_url': approve_url,
        'reject_url': reject_url,
        'site_url': site_url,
    })
    text_body = (
        f"คำขอ{request_type} จาก {requester_name}\n\n"
        + "\n".join(detail_lines)
        + f"\n\nอนุมัติ: {approve_url}"
        + f"\nปฏิเสธ: {reject_url}"
    )
    try:
        send_mail(
            subject=subject,
            message=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            html_message=html_body,
            fail_silently=False,
        )
        return True
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error("send_approval_email failed: %s", exc)
        return False


def build_approval_urls(request_obj, model_type: str, site_url: str) -> tuple[str, str]:
    """Build approve and reject URLs for a request object."""
    approve_token = make_approval_token(model_type, request_obj.pk, 'approve')
    reject_token = make_approval_token(model_type, request_obj.pk, 'reject')
    base = site_url.rstrip('/')
    return (
        f"{base}/approval/{approve_token}/",
        f"{base}/approval/{reject_token}/",
    )
