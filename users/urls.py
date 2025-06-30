from django.urls import path
from .views import (
    RegisterView, VerifyOTPView, LoginView, LogoutView,
    RefreshTokenView, ProfileView, PasswordResetView
)
from .views import ConfirmResetPasswordAPIView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh/', RefreshTokenView.as_view(), name='token_refresh'),
    path('reset-password/', PasswordResetView.as_view(), name='reset_password'),
    path('me/', ProfileView.as_view(), name='profile'),
    path('reset-password/confirm/', ConfirmResetPasswordAPIView.as_view(), name='reset_password_confirm'),
]
