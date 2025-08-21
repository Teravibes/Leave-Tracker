from django.db.models import Q
from django.utils import timezone
from LeaveTracker.models import HolidayRequest
from LeaveTracker.utils.date_utils import count_non_weekend_and_non_holiday_days, total_days_for_queryset
from LeaveTracker.models import HolidayRequest, Event

def get_total_normal_holidays(employee_id, year, public_holiday_dates):
    holiday_requests = HolidayRequest.objects.filter(
        employee_id=employee_id,
        is_special=False,
        status='approved',
        start_date__year=year,
        deleted=None
    ).select_related('employee')  # Optional optimization

    total_days = 0
    for holiday in holiday_requests:
        overlapping_holidays = [
            date for date in public_holiday_dates
            if holiday.start_date <= date <= holiday.end_date
        ]
        duration = count_non_weekend_and_non_holiday_days(
            holiday.start_date, holiday.end_date, overlapping_holidays
        )
        total_days += duration

    return total_days

def get_my_holiday_summary(employee, year):
    # Load public holidays for overlap exclusion
    public_holidays = set(Event.objects.filter(
        start_date__year=year
    ).values_list('start_date', flat=True))

    all_requests = HolidayRequest.objects.filter(
        employee=employee, deleted__isnull=True
    )

    # Filter by year
    this_year_requests = all_requests.filter(
        Q(start_date__year=year) | Q(end_date__year=year),
        reset=False
    )

    approved_regular = this_year_requests.filter(status="approved", is_special=False)
    pending_regular = this_year_requests.filter(status="pending", is_special=False)
    approved_special = this_year_requests.filter(status="approved", is_special=True)
    pending_special = this_year_requests.filter(status="pending", is_special=True)

    # Compute durations
    holidays_taken = total_days_for_queryset(approved_regular, public_holidays) + \
                     total_days_for_queryset(pending_regular, public_holidays)

    special_holidays_taken = total_days_for_queryset(approved_special, public_holidays) + \
                             total_days_for_queryset(pending_special, public_holidays)

    # Categorized tabs
    upcoming_approved = all_requests.filter(
        status="approved", start_date__gte=timezone.now().date()
    )
    past_approved = all_requests.filter(
        status="approved", end_date__lt=timezone.now().date()
    )
    pending = all_requests.filter(status="pending")
    rejected = all_requests.filter(status="rejected")

    return {
        'all_requests': all_requests,
        'approved_regular': approved_regular,
        'pending_regular': pending_regular,
        'approved_special': approved_special,
        'pending_special': pending_special,
        'upcoming_approved': upcoming_approved,
        'past_approved': past_approved,
        'pending': pending,
        'rejected': rejected,
        'holidays_taken': holidays_taken,
        'special_holidays_taken': special_holidays_taken,
        'public_holidays': public_holidays
    }