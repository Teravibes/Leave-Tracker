from LeaveTracker.models import HolidayRequest

def pending_requests(request):
    if request.user.is_authenticated:
        user_groups = request.user.groups.values_list('name', flat=True)
        is_general_manager = any(group in user_groups for group in ['General Manager'])
        is_operations_manager = any(group in user_groups for group in ['Operations Manager'])

        if is_general_manager:
            pending_requests_count = HolidayRequest.objects.filter(status='pending').count()
        elif is_operations_manager:
            group_filter = 'Employee'
            pending_requests_count = HolidayRequest.objects.filter(status='pending', user_group__icontains=group_filter).count()
        else:
            pending_requests_count = 0
    else:
        pending_requests_count = 0

    return {
        'pending_requests_count': pending_requests_count,
    }

def manager(request):
    is_manager = request.user.groups.filter(name__in=['Operations Manager', 'General Manager']).exists()
    pending_requests_count = 0
    if is_manager:
        pending_requests_count = HolidayRequest.objects.filter(status='pending').count()
    return {'is_manager': is_manager, 'pending_requests_count': pending_requests_count}

