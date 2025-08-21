import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from LeaveTracker.models import HolidayRequest
from LeaveTracker.emails.notifications import send_manager_notification
from LeaveTracker.utils.permissions import get_users_with_permission

logger = logging.getLogger('LeaveTracker')

@receiver(post_save, sender=HolidayRequest)
def notify_on_holiday_request(sender, instance, created, **kwargs):
    if not created:
        return

    employee = instance.employee
    user = employee.user

    # Notify the direct manager
    if employee.manager and employee.manager.user.email:
        send_manager_notification(
            employee.manager.user.email,
            user.first_name,
            user.last_name
        )

    # Notify users with permission to review all requests
    try:
        reviewers = get_users_with_permission("LeaveTracker", "review_holiday_requests_all")
        for reviewer in reviewers:
            if reviewer.email:
                send_manager_notification(
                    reviewer.email,
                    user.first_name,
                    user.last_name
                )
    except Exception as e:
        logger.warning(f"Failed to notify reviewers: {str(e)}")
