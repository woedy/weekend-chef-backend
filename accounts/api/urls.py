from django.urls import path

from accounts.api.admin_view import AdminLogin, register_weekend_chef_admin
from accounts.api.chef_views import ChefLogin, register_chef
from accounts.api.client_views import register_client, verify_client_email, resend_client_email_verification, ClientLogin
from accounts.api.password_views import PasswordResetView, confirm_otp_password_view, new_password_reset_view, resend_password_otp

app_name = 'accounts'

urlpatterns = [
    path('register-weekend-chef-admin/', register_weekend_chef_admin, name="register_weekend_chef_admin"),

    path('register-client/', register_client, name="register_client"),
    path('verify-client-email/', verify_client_email, name="verify_client_email"),
    path('resend-client-email-verification/', resend_client_email_verification, name="resend_client_email_verification"),
    path('login-client/', ClientLogin.as_view(), name="login_client"),
    
    
    
    #path('login-chef/', ChefLogin.as_view(), name="login_chef"),
    #path('resend-chef-email-verification/', resend_chef_email_verification, name="resend_chef_email_verification"),

    path('register-chef/', register_chef, name="register_chef"),
    path('login-chef/', ChefLogin.as_view(), name="login_chef"),

    path('login-admin/', AdminLogin.as_view(), name="login_admin"),



    path('forgot-user-password/', PasswordResetView.as_view(), name="forgot_password"),
    path('confirm-password-otp/', confirm_otp_password_view, name="confirm_otp_password"),
    path('resend-password-otp/', resend_password_otp, name="resend_password_otp"),
    path('new-password-reset/', new_password_reset_view, name="new_password_reset_view"),

    #path('remove_user/', remove_user_view, name="remove_user_view"),
   # path('send-sms/', send_sms_view, name="send_sms_view"),

]
