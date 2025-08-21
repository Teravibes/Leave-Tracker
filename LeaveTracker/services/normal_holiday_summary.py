from LeaveTracker.models import Employee, PublicHoliday
from LeaveTracker.services.holiday_summary import get_total_normal_holidays

def compute_total_normal_holidays(user, employee_id, year):
    can_view_all = user.has_perm('LeaveTracker.view_total_normal_holidays_all')
    can_view_managed = user.has_perm('LeaveTracker.view_total_normal_holidays_managed')

    if not (can_view_all or can_view_managed):
        return None, "You don't have permission to view this data."

    if can_view_managed:
        try:
            manager = Employee.objects.get(user=user)
        except Employee.DoesNotExist:
            return None, "Manager record not found."

        if not Employee.objects.filter(manager=manager, id=employee_id).exists():
            return None, "You don't manage this employee."

    public_holidays = list(PublicHoliday.objects.filter(date__year=year).values_list('date', flat=True))
    total_days = get_total_normal_holidays(employee_id, year, public_holidays)

    return total_days, None

def get_remaining_normal_holidays(user, employee_id):
    can_view_all = user.has_perm('LeaveTracker.view_remaining_normal_holidays_all')
    can_view_managed = user.has_perm('LeaveTracker.view_remaining_normal_holidays_managed')

    if not (can_view_all or can_view_managed):
        return None, "You don't have permission to view this data."

    if can_view_managed and not can_view_all:
        try:
            manager = Employee.objects.get(user=user)
        except Employee.DoesNotExist:
            return None, "Manager not found."

        if not Employee.objects.filter(id=employee_id, manager=manager).exists():
            return None, "You don't manage this employee."

    try:
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        return None, "Employee not found"

    return employee.available_holidays, None
