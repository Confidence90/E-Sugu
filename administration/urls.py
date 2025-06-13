# administration/urls.py
from django.urls import path
from .views import AdminStatsView, AdminListingDeleteView, AdminEventDeleteView

urlpatterns = [
    path('stats/', AdminStatsView.as_view(), name='admin-stats'),
    path('listings/<int:id>/', AdminListingDeleteView.as_view(), name='admin-listing-delete'),
    path('events/<int:id>/', AdminEventDeleteView.as_view(), name='admin-event-delete'),
]