from django import template
register = template.Library()
# create tags
@register.filter
def index(indexable, i):
    return indexable[i]