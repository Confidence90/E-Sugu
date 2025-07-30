from django.urls import path, include
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
    ResendOTPView,
    GoogleLoginView,
    CustomGoogleCallbackView,
    FacebookLoginView,
AppleLoginView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-otp/', VerifyUserOTP.as_view(), name='verify-otp'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh-token/', RefreshTokenView.as_view(), name='refresh-token'),
    path('password-reset/', RequestResetPasswordAPIView.as_view(), name='password-reset'),
    path('password-reset/confirm/', ConfirmResetPasswordWithOTPAPIView.as_view(), name='confirm-password'),
    path('password-reset-confirm/<uidb64>/<token>', ConfirmResetPasswordLinkAPIView.as_view(), name='password-reset-confirm'),
    path('set-new-password/', SetNewPassword.as_view(), name='set-new-password'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('me/', TestAuthenticationView.as_view(), name='granted'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    path('google/login/', GoogleLoginView.as_view(), name='google_login'),
    path('google/callback/', CustomGoogleCallbackView, name='google_callback'),
    path('facebook/login/', FacebookLoginView.as_view(), name='facebook_login'),
    path('apple/login/', AppleLoginView.as_view(), name='apple_login'),
    path('accounts/', include('allauth.urls')),
]
