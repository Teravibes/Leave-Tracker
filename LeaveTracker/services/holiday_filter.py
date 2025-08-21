from LeaveTracker.models import HolidayRequest, Employee
from django.db.models import Value, CharField, Case, When
from django.db.models.functions import Concat


def get_filtered_holidays(user, employee_id, year):
    can_filter_all = user.has_perm('LeaveTracker.filter_holidays_all')
    can_filter_managed = user.has_perm('LeaveTracker.filter_holidays_managed')

    if not (can_filter_all or can_filter_managed):
        return None, "You don't have permission to view this data."

    try:
        employee_id = int(employee_id)
        year = int(year)
    except (TypeError, ValueError):
        return None, "Invalid parameters."

    queryset = HolidayRequest.objects.select_related(
        'employee__user', 'special_type'
    ).filter(
        start_date__year=year,
        employee_id=employee_id,
        status='approved',
        deleted__isnull=True
    ).annotate(
        full_name=Concat(
            'employee__user__first_name',
            Value(' '),
            'employee__user__last_name'
        ),
        leave_type=Case(
            When(special_type__name__isnull=True, then=Value('Regular Leave')),
            default='special_type__name',
            output_field=CharField()
        )
    )

    # Apply managed employee restriction
    if not can_filter_all:
        try:
            manager = Employee.objects.get(user=user)
        except Employee.DoesNotExist:
            return None, "You must be linked to an employee profile."
        queryset = queryset.filter(employee__manager=manager)

    results = queryset.order_by('full_name').values_list(
        'full_name', 'start_date', 'end_date', 'days_taken', 'leave_type', 'id'
    )

    data = [list(row) + ["placeholder"] for row in results]  # Placeholder column for JS
    return data, None
