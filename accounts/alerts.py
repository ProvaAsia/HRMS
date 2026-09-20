"""
Real-time security alerting for the HRMS.

Sends email to SECURITY_ALERT_EMAIL when suspicious login activity is
detected.  Uses Django's cache to throttle duplicate alerts so admins
are not flooded when a single account is under sustained attack.

Events:
  - account_locked   : N consecutive failures for one username
  - ip_brute_force   : many failures from a single IP in a short window
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

# How long (seconds) to suppress repeat alerts for the same key
ALERT_COOLDOWN = 30 * 60  # 30 minutes


def _get_ip(request) -> str:
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    return forwarded.split(',')[0].strip() or request.META.get('REMOTE_ADDR', 'unknown')


def _send_alert(subject: str, body: str, throttle_key: str) -> None:
    """Send an email alert, suppressing repeats within ALERT_COOLDOWN."""
    recipients = [
        e.strip()
        for e in getattr(settings, 'SECURITY_ALERT_EMAIL', '').split(',')
        if e.strip()
    ]
    if not recipients:
        logger.warning('SECURITY_ALERT_EMAIL not configured — alert suppressed: %s', subject)
        return

    cache_key = f'sec_alert:{throttle_key}'
    if cache.get(cache_key):
        logger.debug('Security alert throttled: %s', throttle_key)
        return
    cache.set(cache_key, 1, ALERT_COOLDOWN)

    from_email = settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER
    try:
        send_mail(
            subject=f'[HRMS Security] {subject}',
            message=body,
            from_email=from_email,
            recipient_list=recipients,
            fail_silently=True,
        )
        logger.info('Security alert sent: %s → %s', subject, recipients)
    except Exception as exc:
        logger.exception('Failed to send security alert: %s', exc)


def alert_account_locked(request, username: str, failures: int) -> None:
    """Alert when an account is locked after repeated failed logins."""
    ip = _get_ip(request)
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    subject = f'Account locked — {username}'
    body = (
        f'An account has been locked due to repeated failed login attempts.\n\n'
        f'  Username : {username}\n'
        f'  Failures : {failures} consecutive failed logins\n'
        f'  Source IP: {ip}\n'
        f'  Time     : {now}\n\n'
        f'If this was not a legitimate user, the account may be under a brute-force attack.\n\n'
        f'To unlock the account, go to:\n'
        f'{getattr(settings, "SITE_URL", "")}/accounts/login-attempts/\n'
    )
    _send_alert(subject, body, throttle_key=f'locked:{username}')


def alert_ip_brute_force(request, ip: str, attempt_count: int) -> None:
    """Alert when a single IP produces many failures in a short window."""
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    subject = f'Brute-force detected from IP {ip}'
    body = (
        f'Multiple failed login attempts detected from a single IP address.\n\n'
        f'  Source IP      : {ip}\n'
        f'  Failed attempts: {attempt_count} (within the last 10 minutes)\n'
        f'  Time           : {now}\n\n'
        f'Consider blocking this IP at the firewall or Cloudflare level.\n'
    )
    _send_alert(subject, body, throttle_key=f'ip:{ip}')
