# listings/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import * # Ajoutez OrderViewSet

router = DefaultRouter()
router.register(r'listings', ListingViewSet)
router.register(r'orders', OrderViewSet, basename='order')  # 🔥 NOUVEAU

urlpatterns = [
    path('', include(router.urls)),
    path('listings/<int:listing_id>/track-view/', track_listing_view, name='track-listing-view'),
    path('listings/<int:listing_id>/test-tracking/', test_tracking_view, name='test-tracking'),
]