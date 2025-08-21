from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from LeaveTracker.models import HolidayRequest, PublicHoliday, Employee
from LeaveTracker.utils.date_utils import get_month_range
from LeaveTracker.services.normal_holiday_summary import compute_total_normal_holidays, get_remaining_normal_holidays
from LeaveTracker.services.holiday_filter import get_filtered_holidays
import logging

logger = logging.getLogger('LeaveTracker')


@login_required
def get_all_holidays(request):
    try:
        year = request.GET.get('year')
        month = request.GET.get('month')

        if not year or not month:
            logger.warning("Missing year or month parameter.")
            return HttpResponseBadRequest("Missing year or month parameter.")

        year = int(year)
        month = int(month)
        start_date, end_date = get_month_range(year, month)

        # Fetch employee holiday requests in the range
        employee_holidays = []
        employees = Employee.objects.select_related('user').all()

        for employee in employees:
            holidays = HolidayRequest.objects.filter(
                employee=employee,
                status__in=["approved", "pending"],
                start_date__lte=end_date,
                end_date__gte=start_date,
                deleted__isnull=True
            )
            for hr in holidays:
                employee_holidays.append({
                    'employee_name': f"{employee.user.first_name} {employee.user.last_name}",
                    'start_date': hr.start_date.isoformat(),
                    'end_date': hr.end_date.isoformat(),
                    'status': hr.status,
                    'is_special': hr.is_special
                })

        public_holidays_qs = PublicHoliday.objects.filter(
            date__year=year,
            date__month=month
        ).order_by('date')

        public_holidays = [
            {'name': ph.name, 'date': ph.date.isoformat()}
            for ph in public_holidays_qs
        ]

        return JsonResponse({
            'employee_holidays': employee_holidays,
            'public_holidays': public_holidays
        })

    except ValueError:
        logger.warning("Year and month must be integers.")
        return HttpResponseBadRequest("Invalid year or month format.")

    except Exception as e:
        logger.error("Error in get_all_holidays view", exc_info=True)
        return JsonResponse({'error': 'Internal server error'}, status=500)

@login_required
def total_normal_holidays_api(request, employee_id, year):
    total_days, error_msg = compute_total_normal_holidays(request.user, employee_id, year)

    if error_msg:
        return HttpResponseForbidden(error_msg)

    return JsonResponse({"total_days": total_days})

@require_GET
@login_required
def remaining_normal_holidays(request, employee_id):
    remaining_days, error_msg = get_remaining_normal_holidays(request.user, employee_id)

    if error_msg == "Employee not found":
        return JsonResponse({"error": error_msg}, status=404)
    elif error_msg:
        return HttpResponseForbidden(error_msg)

    return JsonResponse({"remaining_days": remaining_days})

@login_required
@require_GET
def filter_holidays(request):
    employee_id = request.GET.get('employee_id')
    year = request.GET.get('year')

    data, error_msg = get_filtered_holidays(request.user, employee_id, year)

    if error_msg:
        if "permission" in error_msg.lower():
            return HttpResponseForbidden(error_msg)
        return JsonResponse({"error": error_msg}, status=400)

    return JsonResponse(data, safe=False)