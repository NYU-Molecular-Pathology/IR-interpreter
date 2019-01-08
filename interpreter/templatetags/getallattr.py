from django import template
register = template.Library()

@register.filter
def getallattr(dictlist, key):
    return([ getattr(d, key) for d in dictlist ])
