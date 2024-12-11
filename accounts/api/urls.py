from django.urls import path

from accounts.api.views import register_user, resend_shop_email_verification, send_sms_view, verify_user_email, resend_email_verification, UserLogin, \
    PasswordResetView, confirm_otp_password_view, resend_password_otp, new_password_reset_view, remove_user_view, \
    ShopLogin, register_bookelu_admin

app_name = 'accounts'

urlpatterns = [
    path('register-user/', register_user, name="register_user"),
    path('register-bookelu-admin/', register_bookelu_admin, name="register_bookelu_admin"),
    path('verify-user-email/', verify_user_email, name="verify_user_email"),
    path('resend-email-verification/', resend_email_verification, name="resend_email_verification"),
    path('resend-shop-email-verification/', resend_shop_email_verification, name="resend_shop_email_verification"),
    path('login-user/', UserLogin.as_view(), name="login_user"),
    path('login-shop/', ShopLogin.as_view(), name="login_shop"),

    path('forgot-user-password/', PasswordResetView.as_view(), name="forgot_password"),
    path('confirm-password-otp/', confirm_otp_password_view, name="confirm_otp_password"),
    path('resend-password-otp/', resend_password_otp, name="resend_password_otp"),
    path('new-password-reset/', new_password_reset_view, name="new_password_reset_view"),

    path('remove_user/', remove_user_view, name="remove_user_view"),
    path('send-sms/', send_sms_view, name="send_sms_view"),

]
