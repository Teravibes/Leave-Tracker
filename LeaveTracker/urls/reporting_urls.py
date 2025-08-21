from django.urls import path
from LeaveTracker.views import reporting, special_holidays

urlpatterns = [
    path('get-special-holiday-usage/', special_holidays.get_special_holiday_usage, name='get_special_holiday_usage'),
    path('special-holiday-usage/', reporting.special_holiday_usage, name='special_holiday_usage'),
    path('export-holidays/', reporting.export_holidays, name='export_holidays'),
]
