from django.urls import path
from LeaveTracker.views import dashboard

urlpatterns = [
    path('', dashboard.home, name='home'),
    path('my-holidays/', dashboard.my_holidays, name='my_holidays'),
    path('get-available-holidays/', dashboard.get_available_holidays, name='get_available_holidays'),
    path('get-user-existing-holidays/', dashboard.get_user_existing_holidays, name='get_user_existing_holidays'),
]
