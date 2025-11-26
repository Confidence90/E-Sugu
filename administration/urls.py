from django.urls import path
from .views import (
    KYCApproveView,
    AdminStatsView,
    AdminListingDeleteView,
    AdminEventDeleteView,
    AdminLogListView
)

urlpatterns = [
    path('kyc-approve/<int:pk>/', KYCApproveView.as_view(), name='kyc-approve'),
    path('admin-stats/', AdminStatsView.as_view(), name='admin-stats'),
    path('admin-delete-listing/<int:id>/', AdminListingDeleteView.as_view(), name='admin-delete-listing'),
    path('admin-delete-event/<int:id>/', AdminEventDeleteView.as_view(), name='admin-delete-event'),
    path('admin-logs/', AdminLogListView.as_view(), name='admin-logs'),
]
