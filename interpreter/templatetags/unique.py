from django import template
register = template.Library()

@register.filter
def unique(items):
    return list(set(items))
