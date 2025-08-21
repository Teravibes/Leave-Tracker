from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from LeaveTracker.models import HolidayRequest
from LeaveTracker.services.holiday_review import approve_holiday_request, reject_holiday_request


@login_required
def review_requests(request):

    can_review_all = request.user.has_perm('LeaveTracker.review_holiday_requests_all')
    can_review_managed = request.user.has_perm('LeaveTracker.review_holiday_requests_managed')

    if not (can_review_all or can_review_managed):
        raise PermissionDenied()

    if can_review_all:
        pending_requests = HolidayRequest.objects.filter(status='pending')
    else:
        pending_requests = HolidayRequest.objects.filter(
            status='pending',
            user_group__icontains='Employee'  # Replace with dynamic group filtering if needed
        )

    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        action = request.POST.get('action')

        if action == 'approve':
            return approve_request(request, request_id)
        elif action == 'reject':
            return reject_request(request, request_id)

    return render(request, 'LeaveTracker/review_requests.html', {
        'pending_requests': pending_requests,
        'is_manager': True,
    })
    
@login_required
def approve_request(request, request_id):
    if not request.user.has_perm('LeaveTracker.approve_holiday_request'):
        raise PermissionDenied()

    approve_holiday_request(request.user, request_id)
    return redirect('review_requests')


@login_required
def reject_request(request, request_id):
    if not request.user.has_perm('LeaveTracker.reject_holiday_request'):
        raise PermissionDenied()

    reject_holiday_request(request.user, request_id)
    return redirect('review_requests')