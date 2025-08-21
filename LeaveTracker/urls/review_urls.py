from django.urls import path
from LeaveTracker.views import review

urlpatterns = [
    path('review-requests/', review.review_requests, name='review_requests'),
    path('approve-request/<int:request_id>/', review.approve_request, name='approve_request'),
    path('reject-request/<int:request_id>/', review.reject_request, name='reject_request'),
]
