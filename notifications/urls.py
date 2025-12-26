# notifications/urls.py
from django.urls import path
from .views import *

urlpatterns = [
    path('', NotificationView.as_view(), name='notifications'),
    path('<int:id>/', NotificationDetailView.as_view(), name='notification-detail'),
    
]