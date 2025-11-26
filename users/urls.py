from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register('admin/users', AdminUserViewSet, basename='admin-user')

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
    path('vendor/profile/', VendorProfileView.as_view(), name='vendor-profile'),
    path('vendor/check-setup/', VendorCheckSetupView.as_view(), name='vendor-check-setup'),
    path('accounts/', include('allauth.urls')),
    path('addresses/', AddressListView.as_view(), name='address-list'),
    path('addresses/<int:pk>/', AddressDetailView.as_view(), name='address-detail'),
    path('addresses/<int:pk>/set-default/', SetDefaultAddressView.as_view(), name='address-set-default'),
    path('regions/', region_list, name='regions'),
    path('vendor/stats/', VendorStatsView.as_view(), name='vendor-stats'),
    path('vendor/sales-report/', VendorSalesReportView.as_view(), name='vendor-sales-report'),
    path('vendor/performance/', VendorPerformanceView.as_view(), name='vendor-performance'),
    path('vendor/quick-stats/', vendor_quick_stats, name='vendor-quick-stats'),
    path('vendor/check-status/', check_vendor_status, name='vendor-check-status'),
    path('vendor/activate/', activate_vendor_status, name='vendor-activate'),
    path('vendor/create-profile/', create_vendor_profile, name='vendor-create-profile'),
    path('vendor/debug-user-info/', debug_user_info, name='vendor-debug-user-info'),
    
    # 🔥 AJOUT DES URLs MANQUANTES :
    path('check-admin-permission/', check_admin_permission, name='check-admin-permission'),
    path('check-listing-permission/', check_listing_permission, name='check-listing-permission'),
    path('vendor/debug-visitors/', debug_visitor_stats, name='debug-visitors'),
    path('vendor/test-visitor-data/', test_visitor_data, name='test-visitor-data'),
    path('track-dashboard-view/', track_dashboard_view, name='track-dashboard-view'),
    
    # URLs Admin
    path('admin/stats/', AdminUserViewSet.as_view({'get': 'stats'}), name='admin-stats'),
    path('admin/users/', admin_users_list, name='admin-users-list'),
    path('admin/users/<int:user_id>/', admin_update_user, name='admin-update-user'),
    path('admin/stats/', admin_users_stats, name='admin-users-stats'),
    path('admin/dashboard/stats/', admin_dashboard_stats, name='admin-dashboard-stats'),
    path('admin/dashboard/recent-orders/', admin_recent_orders, name='admin-recent-orders'),
    path('admin/dashboard/top-vendors/', admin_top_vendors, name='admin-top-vendors'),
    
] + router.urls