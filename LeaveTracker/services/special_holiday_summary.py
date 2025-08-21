from LeaveTracker.models import SpecialHolidayUsage
from django.db.models import Sum

def get_special_holiday_usage_data(employee_id=None, year=None):
    usage_queryset = SpecialHolidayUsage.objects.all()

    if employee_id:
        usage_queryset = usage_queryset.filter(employee__id=employee_id)
    if year:
        usage_queryset = usage_queryset.filter(year=year)

    return list(usage_queryset.values(
        'employee__user__first_name',
        'employee__user__last_name',
        'employee__user__email',
        'holiday_type__name',
        'year'
    ).annotate(total_days_used=Sum('days_used')))
