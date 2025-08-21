import pytest
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from LeaveTracker.models import HolidayRequest
from LeaveTracker.utils.permissions import get_users_with_permission

@pytest.mark.django_db
def test_get_users_with_permission_via_group():
    # Create permission
    content_type = ContentType.objects.get_for_model(HolidayRequest)
    perm = Permission.objects.get(
        codename="approve_holiday_request",
        content_type=content_type
    )

    # Create group and assign permission
    group = Group.objects.create(name="TestGroup")
    group.permissions.add(perm)

    # Create user and assign group
    user = User.objects.create_user(username="testuser", email="test@example.com", password="123")
    user.groups.add(group)

    # Call the utility function
    result = get_users_with_permission("LeaveTracker", "approve_holiday_request")

    # Check
    assert user in result
    
@pytest.mark.django_db
def test_get_users_with_permission_excludes_unprivileged_users():
    # Setup: create the relevant permission
    content_type = ContentType.objects.get_for_model(HolidayRequest)
    perm = Permission.objects.get(
        codename="approve_holiday_request",
        content_type=content_type
    )

    # Create user WITHOUT permission
    user = User.objects.create_user(username="unauthorized_user", email="nope@example.com", password="123")

    # Run the utility
    result = get_users_with_permission("LeaveTracker", "approve_holiday_request")

    # Check that unauthorized user is NOT in the result
    assert user not in result
