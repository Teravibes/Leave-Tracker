import pytest
from unittest.mock import patch
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from LeaveTracker.models import HolidayRequest, Employee
from datetime import date

@pytest.mark.django_db
@patch("LeaveTracker.signals.notifications.send_manager_notification")
def test_notify_on_holiday_request(mock_notify):
    # Create approving permission and assign to a group
    content_type = ContentType.objects.get_for_model(HolidayRequest)
    perm = Permission.objects.get(
        codename="review_holiday_requests_all",
        content_type=content_type
    )
    group = Group.objects.create(name="Reviewers")
    group.permissions.add(perm)

    # Create a manager with permission
    manager_user = User.objects.create_user(username="manager", email="manager@example.com")
    manager_user.groups.add(group)

    # Create an employee whose manager is that user
    employee_user = User.objects.create_user(username="employee", email="employee@example.com")
    manager_employee = Employee.objects.create(user=manager_user)
    employee = Employee.objects.create(user=employee_user, manager=manager_employee)

    # Create the HolidayRequest (this should trigger the signal)
    HolidayRequest.objects.create(
        employee=employee,
        days_taken=3,
        start_date=date(2025, 7, 20),
        end_date=date(2025, 7, 22)
    )

    # Now assert: send_manager_notification was called
    assert mock_notify.call_count >= 1

    # Optional: check who was notified
    notified_emails = [call.args[0] for call in mock_notify.call_args_list]
    assert "manager@example.com" in notified_emails
