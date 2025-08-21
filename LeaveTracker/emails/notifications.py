from django.conf import settings
from LeaveTracker.emails.utils import send_custom_email


def send_employee_notification(employee_email, is_approved):
    status = "Approved" if is_approved else "Rejected"
    subject = f"Holiday Request {status}"

    context = {
        "status": status,
        "subject": subject,
    }

    send_custom_email(
        subject=subject,
        to_email=employee_email,
        context=context,
        html_template="emails/employee_notification.html"
    )



def send_manager_notification(manager_email, employee_firstname, employee_lastname):
    employee_fullname = f"{employee_firstname} {employee_lastname}"
    subject = f"New Holiday Request: {employee_fullname}"

    context = {
        "employee_fullname": employee_fullname,
        "view_request_url": getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000/'),
        "subject": subject
    }

    send_custom_email(
        subject=subject,
        to_email=manager_email,
        context=context,
        html_template="emails/manager_notification.html"
    )
