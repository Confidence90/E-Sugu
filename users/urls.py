from django.urls import path
from .views import (
    RegisterView,
    VerifyUserOTP,  # anciennement VerifyUserEmail
    LoginView,
    LogoutView,
    RefreshTokenView,
    ProfileView,
    RequestResetPasswordAPIView,
    ConfirmResetPasswordLinkAPIView,
    ConfirmResetPasswordWithOTPAPIView,
    TestAuthenticationView,
    SetNewPassword,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-otp/', VerifyUserOTP.as_view(), name='verify-otp'),  # renommé
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh-token/', RefreshTokenView.as_view(), name='refresh-token'),
    path('password-reset/', RequestResetPasswordAPIView.as_view(), name='password-reset'),
    path('password-reset/confirm/', ConfirmResetPasswordLinkAPIView.as_view(), name='confirm-password-otp'),
    path('password-reset-confirm/<uidb64>/<token>', ConfirmResetPasswordLinkAPIView.as_view(), name='password-reset-confirm'),
    path('set-new-password/', SetNewPassword.as_view(), name='set-new-password'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('me/', TestAuthenticationView.as_view(), name='granted'),
]
