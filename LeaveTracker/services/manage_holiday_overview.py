from LeaveTracker.models import Employee, HolidayRequest, Event
from LeaveTracker.utils.date_utils import count_non_weekend_and_non_holiday_days
from datetime import datetime

def get_manage_holiday_overview(current_user, can_view_all, can_view_managed, year=None, employee_id=None):
    current_year = datetime.now().year
    public_holiday_dates = Event.objects.filter(
        start_date__year=current_year
    ).values_list('start_date', flat=True)

    # Employee scope
    if can_view_all:
        employees = Employee.objects.all()
        approved_requests = HolidayRequest.objects.filter(
            status='approved',
            deleted__isnull=True
        ).order_by('start_date')
    elif can_view_managed:
        manager = Employee.objects.get(user=current_user)
        employees = Employee.objects.filter(manager=manager)
        approved_requests = HolidayRequest.objects.filter(
            status='approved',
            employee__in=employees,
            deleted__isnull=True
        ).order_by('start_date')
    else:
        return {}, [], [], current_year  # Permission fallback

    # Filters
    if employee_id:
        approved_requests = approved_requests.filter(employee__id=employee_id)
    if year:
        approved_requests = approved_requests.filter(start_date__year=year)
    else:
        year = current_year

    # Context preparation
    employee_holidays_data = {}
    for employee in employees:
        requests = approved_requests.filter(employee=employee)

        if year:
            requests = requests.filter(start_date__year=year)

        approved = requests.filter(status="approved", reset=False, is_special=False)
        pending = requests.filter(status="pending", reset=False, is_special=False)

        approved_length = sum([
            count_non_weekend_and_non_holiday_days(hr.start_date, hr.end_date, public_holiday_dates)
            for hr in approved
        ])

        pending_length = sum([
            count_non_weekend_and_non_holiday_days(hr.start_date, hr.end_date, public_holiday_dates)
            for hr in pending
        ])

        special = requests.filter(is_special=True)
        if year:
            special = special.filter(start_date__year=year)

        special_length = sum([
            count_non_weekend_and_non_holiday_days(hr.start_date, hr.end_date, public_holiday_dates)
            for hr in special
        ])

        special_types = list(special.values_list('special_type__name', flat=True).distinct())

        employee_holidays_data[employee] = {
            'total_holidays': approved_length + pending_length,
            'special_holidays': special_length,
            'special_types': special_types,
        }

    return employee_holidays_data, employees, approved_requests, year
