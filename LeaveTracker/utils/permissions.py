from django.contrib.auth.models import User
from django.db.models import Q

def get_users_with_permission(app_label: str, codename: str):
    """
    Returns a queryset of users who have the specified permission,
    either directly or via their group.
    
    """
    return User.objects.filter(
        Q(user_permissions__codename=codename, user_permissions__content_type__app_label=app_label) |
        Q(groups__permissions__codename=codename, groups__permissions__content_type__app_label=app_label)
    ).distinct()
