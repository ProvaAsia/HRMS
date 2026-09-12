from django import template

register = template.Library()


@register.filter
def key(d, k):
    """Get a value from a dict by key in a template: {{ my_dict|key:some_var }}"""
    if isinstance(d, dict):
        return d.get(k, '')
    return ''
