from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from openpyxl.styles import Font
import openpyxl
import datetime
import requests
from LeaveTracker.models import HolidayRequest, PublicHoliday
from LeaveTracker.services.special_holiday_summary import get_special_holiday_usage_data
from LeaveTracker.services.holiday_export import generate_holiday_export_workbook


@login_required
def export_holidays(request):
    year = request.GET.get('year')
    workbook, error = generate_holiday_export_workbook(request.user, year)

    if error:
        if "permission" in error.lower():
            return HttpResponseForbidden(error)
        return JsonResponse({"error": error}, status=400)

    # Prepare HTTP Excel response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="holidays_{year}.xlsx"'
    workbook.save(response)
    return response

@login_required
def special_holiday_usage(request):
    user = request.user
    can_view_all = user.has_perm('LeaveTracker.view_special_holiday_usage_all')
    can_view_managed = user.has_perm('LeaveTracker.view_special_holiday_usage_managed')

    if not (can_view_all or can_view_managed):
        return HttpResponseForbidden("You don't have permission to view this data.")

    employee_id = request.GET.get('employee_id')
    year = request.GET.get('year')

    usage_data = get_special_holiday_usage_data(employee_id, year)

    # Optionally, clean up names or formats
    formatted_data = []
    for entry in usage_data:
        full_name = f"{entry['employee__user__first_name']} {entry['employee__user__last_name']}"
        formatted_data.append({
            'full_name': full_name,
            'holiday_type__name': entry['holiday_type__name'],
            'total_days_used': entry['total_days_used'],
            'year': entry['year'],
            'email': entry['employee__user__email'],
        })

    return JsonResponse({'data': formatted_data})