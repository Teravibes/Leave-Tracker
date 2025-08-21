from django.urls import path
from LeaveTracker.views import api

urlpatterns = [
    path('get-all-holidays/', api.get_all_holidays, name='get_all_holidays'),
    path('total-normal-holidays/<int:employee_id>/<int:year>/', api.total_normal_holidays_api, name='total_normal_holidays_api'),
    path('remaining-normal-holidays/<int:employee_id>/', api.remaining_normal_holidays, name='remaining_normal_holidays'),
    path('filter-holidays/', api.filter_holidays, name='filter_holidays'),
]
