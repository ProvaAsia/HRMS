"""
Simple rate limiter using Django's cache backend.
Drop-in replacement for django-ratelimit that needs no extra package.

Usage:
    from hrms.ratelimit import is_rate_limited

    def my_view(request):
        if is_rate_limited(request, key='ip', rate='10/m'):
            return HttpResponse('Too many requests', status=429)
        ...
"""
import time
from django.core.cache import cache


def _parse_rate(rate: str):
    """Parse '10/m' → (10, 60), '5/h' → (5, 3600)."""
    count, period = rate.split('/')
    count = int(count)
    periods = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
    return count, periods[period[0]]


def is_rate_limited(request, key: str, rate: str, method: str = 'POST') -> bool:
    """
    Return True if this request should be blocked.

    key  : 'ip' or 'user'
    rate : e.g. '10/m', '5/h', '100/d'
    """
    if method != 'ALL' and request.method != method:
        return False

    limit, period = _parse_rate(rate)

    if key == 'ip':
        ident = (
            request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            or request.META.get('REMOTE_ADDR', 'unknown')
        )
    elif key == 'user':
        ident = str(request.user.pk) if request.user.is_authenticated else (
            request.META.get('REMOTE_ADDR', 'unknown')
        )
    else:
        ident = key

    cache_key = f'rl:{key}:{ident}:{rate}'
    now = int(time.time())
    window = now // period

    hits_key = f'{cache_key}:{window}'
    count = cache.get(hits_key, 0)
    if count >= limit:
        return True
    cache.set(hits_key, count + 1, period * 2)  # TTL = 2× window
    return False
