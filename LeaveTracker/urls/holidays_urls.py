from django.urls import path
from LeaveTracker.views import holidays

urlpatterns = [
    path('submit-holiday-request/', holidays.submit_holiday_request, name='submit_holiday_request'),
    path('manage-holidays/', holidays.manage_holidays, name='manage_holidays'),
    path('delete-holiday/<int:holiday_id>/', holidays.delete_holiday, name='delete_holiday'),
]
