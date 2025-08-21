from django import template

register = template.Library()


@register.filter
def as_integer(value):
    return int(value) if value else 0


@register.filter
def subtract(value, arg):
    return value - arg
