from django import template

register = template.Library()


@register.filter
def key(d, k):
    """{{ my_dict|key:some_var }}"""
    if isinstance(d, dict):
        return d.get(k, '')
    return ''


@register.filter
def split(value, sep=' '):
    """{{ "a b c"|split:" " }}"""
    return value.split(sep)
