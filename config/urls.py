from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Include each sub-urlconf explicitly
    path('', include('LeaveTracker.urls.dashboard_urls')),
    path('', include('LeaveTracker.urls.auth_urls')),
    path('', include('LeaveTracker.urls.holidays_urls')),
    path('', include('LeaveTracker.urls.review_urls')),
    path('', include('LeaveTracker.urls.reporting_urls')),
    path('', include('LeaveTracker.urls.api_urls')),
]