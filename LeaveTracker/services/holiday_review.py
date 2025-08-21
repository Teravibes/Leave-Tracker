from django.utils import timezone
from django.shortcuts import get_object_or_404
from LeaveTracker.models import HolidayRequest, SpecialHolidayUsage
from LeaveTracker.emails.notifications import send_employee_notification


def approve_holiday_request(user, request_id):
    holiday_request = get_object_or_404(HolidayRequest, id=request_id)

    holiday_request.status = 'approved'
    holiday_request.approved_by = user
    holiday_request.approved_at = timezone.now()
    holiday_request.save()

    send_employee_notification(holiday_request.employee.user.email, is_approved=True)
    return holiday_request


def reject_holiday_request(user, request_id):
    holiday_request = get_object_or_404(HolidayRequest, id=request_id)

    holiday_request.status = 'rejected'
    holiday_request.rejected_by = user
    holiday_request.rejected_at = timezone.now()
    holiday_request.save()

    employee = holiday_request.employee
    days_rejected = holiday_request.days_taken

    if holiday_request.is_special and holiday_request.special_type:
        year = holiday_request.start_date.year
        usage, _ = SpecialHolidayUsage.objects.get_or_create(
            employee=employee,
            holiday_type=holiday_request.special_type,
            year=year
        )
        usage.days_used = max(usage.days_used - days_rejected, 0)
        usage.save()
    else:
        employee.available_holidays += days_rejected
        employee.save()

    send_employee_notification(employee.user.email, is_approved=False)
    return holiday_request