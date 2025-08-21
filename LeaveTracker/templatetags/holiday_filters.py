from django import template

register = template.Library()


@register.filter
def holiday_status_badge_class(status):
    status_badge_classes = {
        'pending': 'bg-warning text-dark',
        'approved': 'bg-success',
        'rejected': 'bg-danger',
    }
    return status_badge_classes.get(status, '')


@register.filter(name='has_perm')
def has_perm(user, perm_name):
    return user.has_perm(perm_name)
