from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from datetime import datetime
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator
import logging
from LeaveTracker.services.holiday_summary import get_my_holiday_summary
from LeaveTracker.services.home_summary import rollover_annual_holidays, get_employee_dashboard_summary
from LeaveTracker.models import Employee, HolidayRequest
from LeaveTracker.forms import HolidayRequestForm


logger = logging.getLogger('LeaveTracker')


@login_required
def home(request):
    try:
        # Run rollover and reset logic once per year
        rollover_annual_holidays()

        summary = get_employee_dashboard_summary(request.user)

        # Permissions
        is_manager = request.user.has_perm('LeaveTracker.is_manager')
        can_review_managed = request.user.has_perm('LeaveTracker.review_holiday_requests_managed')
        can_review_all = request.user.has_perm('LeaveTracker.review_holiday_requests_all')
        can_view_all_employees = request.user.has_perm('LeaveTracker.view_all_employees')
        can_view_managed_employees = request.user.has_perm('LeaveTracker.view_managed_employees')

        # Handle form submission
        if request.method == 'POST':
            form = HolidayRequestForm(request.POST)
            if form.is_valid():
                start_date = form.cleaned_data["start_date"]
                end_date = form.cleaned_data["end_date"]

                overlapping = summary['holiday_requests'].filter(
                    start_date__lte=end_date,
                    end_date__gte=start_date
                ).exists()

                if overlapping:
                    messages.error(request, "You have already requested holidays for the selected days.")
                else:
                    holiday_request = form.save(commit=False)
                    holiday_request.employee = summary['employee']
                    holiday_request.status = 'pending'
                    holiday_request.save()
                    return redirect('home')
        else:
            form = HolidayRequestForm()

        context = {
            'form': form,
            'holiday_requests': summary['holiday_requests'],
            'available_holidays': summary['employee'].available_holidays,
            'is_manager': is_manager,
            'holidays_taken': summary['holidays_taken'],
            'special_holiday_types': summary['special_holiday_types'],
            'can_review_managed': can_review_managed,
            'can_review_all': can_review_all,
            'can_view_all_employees': can_view_all_employees,
            'can_view_managed_employees': can_view_managed_employees
        }

        return render(request, 'LeaveTracker/home.html', context)

    except Exception as e:
        logger.error(f"Error in home view: {str(e)}")
        return HttpResponse("An error occurred. Please try again later.", status=500)


@login_required
def get_available_holidays(request):
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee record not found.'}, status=404)

    return JsonResponse({'available_holidays': employee.available_holidays})

@login_required
def my_holidays(request):
    employee = Employee.objects.select_related('user').get(user=request.user)
    is_manager = request.user.has_perm('LeaveTracker.is_manager')
    year = int(request.GET.get('year', datetime.now().year))

    summary = get_my_holiday_summary(employee, year)

    # Pagination
    page_number = request.GET.get('page', 1)
    paginate = lambda qs: Paginator(qs.order_by('start_date'), 10).get_page(page_number)

    context = {
        'upcoming_approved_holidays': paginate(summary['upcoming_approved']),
        'past_holidays': paginate(summary['past_approved']),
        'pending_holidays': paginate(summary['pending']),
        'rejected_holidays': paginate(summary['rejected']),
        'holidays_taken': summary['holidays_taken'],
        'special_holidays_taken': summary['special_holidays_taken'],
        'years': [d.year for d in summary['all_requests'].dates('start_date', 'year').distinct()],
        'selected_year': year,
        'is_manager': is_manager,
    }

    return render(request, 'LeaveTracker/my-holidays.html', context)


def get_user_existing_holidays(request):
    employee = Employee.objects.get(user=request.user)
    past_holidays = HolidayRequest.objects.filter(
        employee=employee, status__in=['pending', 'approved'], deleted__isnull=True)
    holidays = []
    for holiday in past_holidays:
        holidays.append({
            'start_date': holiday.start_date,
            'end_date': holiday.end_date,
            'deleted': holiday.deleted
        })
    return JsonResponse({'past_holidays': holidays})