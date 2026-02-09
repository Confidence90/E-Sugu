# notifications/urls.py
from django.urls import path
from .views import (
    NotificationView,
    NotificationDetailView,
    AdminNotificationView,
    AdminNotificationDetailView,
    AdminNotificationBulkView,
    AdminSendNotificationView,
    AdminNotificationStatsView,
)

urlpatterns = [
    path('', NotificationView.as_view(), name='notifications'),
    path('<int:id>/', NotificationDetailView.as_view(), name='notification-detail'),
    path('admin/', AdminNotificationView.as_view(), name='admin-notifications'),
    path('admin/<int:id>/', AdminNotificationDetailView.as_view(), name='admin-notification-detail'),
    path('admin/bulk/', AdminNotificationBulkView.as_view(), name='admin-notification-bulk'),
    path('admin/send/', AdminSendNotificationView.as_view(), name='admin-send-notification'),
    path('admin/stats/', AdminNotificationStatsView.as_view(), name='admin-notification-stats'),
]