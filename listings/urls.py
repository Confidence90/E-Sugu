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
    path('admin/stats/', admin_products_stats, name='admin-products-stats'),
    path('admin/bulk-update/', admin_bulk_update_products, name='admin-bulk-update-products'),
    path('admin/bulk-delete/', admin_bulk_delete_products, name='admin-bulk-delete-products'),
    path('listings/<int:pk>/update/', ListingViewSet.as_view({'put': 'update_listing', 'patch': 'update_listing'}), name='listing-update'),
    path('listings/<int:pk>/delete/', ListingViewSet.as_view({'delete': 'delete_listing'}), name='listing-delete'),
    path('listings/bulk-delete/', ListingViewSet.as_view({'post': 'bulk_delete'}), name='listing-bulk-delete'),
    path('listings/<int:pk>/toggle-status/', ListingViewSet.as_view({'post': 'toggle_status'}), name='listing-toggle-status'),
    path('listings/<int:pk>/delete-image/', ListingViewSet.as_view({'delete': 'delete_image'}), name='listing-delete-image'),
    path('my-listings/', ListingViewSet.as_view({'get': 'my_listings'}), name='my-listings'),
]