import openpyxl
from openpyxl.styles import Font
from LeaveTracker.models import HolidayRequest

def generate_holiday_export_workbook(user, year):
    can_view_all = user.has_perm('LeaveTracker.view_all_employees')
    can_view_some = user.has_perm('LeaveTracker.view_holiday')

    if not (can_view_all or can_view_some):
        return None, "You don't have permission to export holiday data."

    try:
        year = int(year)
    except (TypeError, ValueError):
        return None, "Invalid year parameter."

    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Holidays"

    # Header
    header = ["Employee", "Start Date", "End Date", "Days Taken", "Holiday Type"]
    ws.append(header)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    # Query holidays
    holidays = HolidayRequest.objects.select_related('employee__user', 'special_type').filter(
        status='approved',
        deleted__isnull=True,
        start_date__year=year
    )

    for holiday in holidays:
        holiday_type = (
            f"Special Holiday - {holiday.special_type.name}"
            if holiday.is_special and holiday.special_type else
            "Regular Holiday"
        )

        ws.append([
            holiday.employee.user.get_full_name(),
            holiday.start_date.strftime("%Y-%m-%d"),
            holiday.end_date.strftime("%Y-%m-%d"),
            holiday.days_taken,
            holiday_type
        ])

    return wb, None
