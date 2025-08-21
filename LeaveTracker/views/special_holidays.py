from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Sum, CharField, Value
from django.db.models.functions import Concat
from LeaveTracker.models import SpecialHolidayTypes, SpecialHolidayUsage, Employee

@login_required
def get_special_holiday_usage(request):
    try:
        special_type_id = int(request.GET.get("special_type_id"))
        year = int(request.GET.get("year"))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid parameters."}, status=400)

    try:
        special_type = SpecialHolidayTypes.objects.get(id=special_type_id)
    except SpecialHolidayTypes.DoesNotExist:
        return JsonResponse({"error": "Special holiday type not found."}, status=404)

    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        return JsonResponse({"error": "Employee profile not found."}, status=404)

    usage = SpecialHolidayUsage.objects.filter(
        employee=employee, holiday_type=special_type, year=year
    ).first()

    return JsonResponse({
        "max_days": special_type.max_days,
        "used_days": usage.days_used if usage else 0
    })
    
@login_required
def special_holiday_usage(request):
    # Check if the user has the necessary permissions
    can_view_all = request.user.has_perm('LeaveTracker.view_special_holiday_usage_all')
    can_view_managed = request.user.has_perm('LeaveTracker.view_special_holiday_usage_managed')

    if not (can_view_all or can_view_managed):
        return HttpResponseForbidden("You don't have permission to view this page.")

    # Validate input parameters
    employee_id = request.GET.get('employee_id', None)
    year = request.GET.get('year', None)

    if not (employee_id and year):
        return JsonResponse({"error": "Missing parameters."}, status=400)

    try:
        year = int(year)
    except ValueError:
        return JsonResponse({"error": "Invalid year."}, status=400)

    # Base queryset
    usage_qs = SpecialHolidayUsage.objects.filter(
        year=year,
        holiday_type__isnull=False
    ).annotate(
        full_name=Concat(
            'employee__user__first_name',
            Value(' '),
            'employee__user__last_name',
            output_field=CharField()
        )
    )

    # Restrict to managed employees if not allowed to view all
    if not can_view_all:
        usage_qs = usage_qs.filter(employee__manager__user=request.user)

    # Filter by specific employee unless "all"
    if employee_id != 'all':
        try:
            employee_id = int(employee_id)
            usage_qs = usage_qs.filter(employee_id=employee_id)
        except ValueError:
            return JsonResponse({"error": "Invalid employee ID."}, status=400)

    # Annotate + exclude zero-usage entries
    usage_data = usage_qs.values(
        'full_name', 'year', 'holiday_type__name'
    ).annotate(
        total_days_used=Sum('days_used')
    ).filter(
        total_days_used__gt=0  # 👈 Filter out zero-usage records
    ).order_by('full_name')

    return JsonResponse({'data': list(usage_data)}, safe=False)