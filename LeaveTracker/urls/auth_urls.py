from django.urls import path
from django.contrib.auth import views as auth_views
from LeaveTracker.views import auth

urlpatterns = [
    path('login/', auth.login_user, name='login'),
    path('logout/', auth.logout_user, name='logout'),


    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name="registration/password_reset_form.html",
             html_email_template_name="registration/password_reset_email.html",
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html"),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"),
         name='password_reset_complete'),
]
