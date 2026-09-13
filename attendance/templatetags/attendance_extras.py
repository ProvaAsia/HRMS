from django import template
register = template.Library()

@register.filter
def key(d, k):
    if isinstance(d, dict):
        return d.get(k, '')
    return ''

@register.filter
def split(value, sep=' '):
    return value.split(sep)
