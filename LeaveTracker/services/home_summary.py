
from django.db.models import Q, Sum
from django.utils import timezone
from LeaveTracker.models import Employee, HolidayRequest, SpecialHolidayTypes

def rollover_annual_holidays():
    today = timezone.now().date()
    current_year = today.year

    employees = Employee.objects.all()

    for employee in employees:
        if employee.last_holiday_year_update < current_year:
            employee.available_holidays += employee.annual_holidays
            employee.last_holiday_year_update = current_year
            employee.save()

            # Reset approved holidays from previous years
            HolidayRequest.objects.filter(
                employee=employee,
                status="approved",
                reset=False,
                start_date__year__lt=current_year,
                deleted__isnull=True
            ).update(reset=True)


def get_employee_dashboard_summary(user):
    today = timezone.now().date()
    current_year = today.year

    employee = Employee.objects.get(user=user)
    holiday_requests = HolidayRequest.objects.filter(
        employee=employee,
        deleted__isnull=True
    )

    this_year_requests = holiday_requests.filter(
        Q(start_date__year=current_year) | Q(end_date__year=current_year),
        reset=False,
        is_special=False
    )

    next_year_requests = holiday_requests.filter(
        Q(start_date__year=current_year + 1) | Q(end_date__year=current_year + 1),
        reset=False,
        is_special=False
    )

    holidays_taken = 0
    for holiday_set in [this_year_requests, next_year_requests]:
        approved = holiday_set.filter(status="approved").aggregate(total_days=Sum('days_taken'))['total_days'] or 0
        pending = holiday_set.filter(status="pending").aggregate(total_days=Sum('days_taken'))['total_days'] or 0
        holidays_taken += approved + pending

    return {
        'employee': employee,
        'holiday_requests': holiday_requests,
        'holidays_taken': holidays_taken,
        'special_holiday_types': SpecialHolidayTypes.objects.all()
    }