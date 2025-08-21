from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.core.paginator import Paginator
from django.db.models import Case, When, Value, CharField
from django.db.models.functions import Concat
import json
from datetime import datetime
from django.utils import timezone
from django.core.exceptions import PermissionDenied
import logging
from LeaveTracker.models import HolidayRequest, Employee, PublicHoliday, SpecialHolidayUsage
from LeaveTracker.utils.date_utils import count_non_weekend_and_non_holiday_days
from LeaveTracker.services.holiday_submission import process_holiday_submission
from LeaveTracker.services.manage_holiday_overview import get_manage_holiday_overview

logger = logging.getLogger('LeaveTracker')


@csrf_exempt
@login_required
def submit_holiday_request(request):
    if request.method == "POST":
        data = json.loads(request.body)
        response = process_holiday_submission(request.user, data)
        return JsonResponse(response)
    return JsonResponse({"status": "error", "message": "Invalid request method"})

@login_required
def delete_holiday(request, holiday_id):
    if not request.user.has_perm('LeaveTracker.delete_holiday'):
        message = (
            "You can view this page but don't have permission to delete."
            if request.user.has_perm('LeaveTracker.view_holiday') else
            "You don't have permission to perform this action."
        )
        return render(request, "403.html", {"custom_message": message}, status=403)

    # Fetch holiday
    holiday_request = get_object_or_404(
        HolidayRequest.objects.select_related('employee'),
        id=holiday_id
    )

    employee = holiday_request.employee

    # Calculate non-holiday weekdays
    public_holidays_dates = list(PublicHoliday.objects.filter(
        date__range=[holiday_request.start_date, holiday_request.end_date]
    ).values_list('date', flat=True))

    days_deleted = count_non_weekend_and_non_holiday_days(
        holiday_request.start_date,
        holiday_request.end_date,
        public_holidays_dates
    )

    if holiday_request.is_special and holiday_request.special_type:
        year = holiday_request.start_date.year
        usage, _ = SpecialHolidayUsage.objects.get_or_create(
            employee=employee,
            holiday_type=holiday_request.special_type,
            year=year
        )
        usage.days_used = max(0, usage.days_used - days_deleted)
        usage.save()
    else:
        employee.available_holidays += days_deleted
        employee.save()

    # Soft delete
    holiday_request.deleted = timezone.now()
    holiday_request.deleted_by = request.user
    holiday_request.save()

    return JsonResponse({'status': 'ok'})

@login_required
def manage_holidays(request):
    can_view_all = request.user.has_perm('LeaveTracker.view_all_employees')
    can_view_managed = request.user.has_perm('LeaveTracker.view_managed_employees')
    can_view_only = request.user.has_perm('LeaveTracker.view_holiday')

    if not (can_view_all or can_view_managed or can_view_only):
        raise PermissionDenied()

    employee_id = request.GET.get('employee_id')
    year = request.GET.get('year')

    employee_holidays_data, employees, approved_requests, selected_year = get_manage_holiday_overview(
        request.user, can_view_all, can_view_managed, year=year, employee_id=employee_id
    )

    paginator = Paginator(approved_requests, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    years = [d.year for d in HolidayRequest.objects.dates('start_date', 'year')]

    context = {
        'page_obj': page_obj,
        'is_manager': can_view_all or can_view_managed,
        "can_delete_holiday": request.user.has_perm("LeaveTracker.delete_holiday"),
        'employee_holidays_data': employee_holidays_data,
        'employees': employees,
        'years': years,
        'view_only': can_view_only,
        'now': datetime.now(),
    }

    return render(request, 'LeaveTracker/manage_holidays.html', context)

@login_required
@require_GET
def filter_holidays(request):
    # Permissions
    can_filter_all = request.user.has_perm('LeaveTracker.filter_holidays_all')
    can_filter_managed = request.user.has_perm('LeaveTracker.filter_holidays_managed')

    if not (can_filter_all or can_filter_managed):
        raise PermissionDenied()

    # Parameter validation
    try:
        employee_id = int(request.GET.get('employee_id'))
        year = int(request.GET.get('year'))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid parameters."}, status=400)

    # Base query
    base_query = HolidayRequest.objects.select_related('employee__user', 'special_type').filter(
        start_date__year=year,
        employee_id=employee_id,
        status='approved',
        deleted__isnull=True
    ).annotate(
        full_name=Concat('employee__user__first_name', Value(' '), 'employee__user__last_name'),
        leave_type=Case(
            When(special_type__name__isnull=True, then=Value('Regular Leave')),
            default='special_type__name',
            output_field=CharField(),
        )
    )

    # Restrict if managed-only
    if not can_filter_all:
        try:
            employee = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            return HttpResponseForbidden("You must be linked to an employee profile.")
        base_query = base_query.filter(employee__manager=employee)

    # Format data
    filtered_holidays = base_query.order_by('full_name').values_list(
        'full_name', 'start_date', 'end_date', 'days_taken', 'leave_type', 'id'
    )

    new_data = []
    for row in filtered_holidays:
        row_as_list = list(row)
        row_as_list.append("placeholder")  # Modify/remove depending on JS needs
        new_data.append(row_as_list)

    return JsonResponse(new_data, safe=False)
