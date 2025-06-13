# users/urls.py
from django.urls import path
from .views import RegisterView, VerifyOTPView, LoginView, LogoutView, RefreshTokenView, PasswordResetView, ProfileView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh/', RefreshTokenView.as_view(), name='refresh'),
    path('password-reset/', PasswordResetView.as_view(), name='password-reset'),
    path('me/', ProfileView.as_view(), name='profile'),
]