from django import template
import sys
register = template.Library()

@register.filter
def unique(items):
  return list(set(items))
  # sys.stderr.write(str(type(items)))
  # return(items)
