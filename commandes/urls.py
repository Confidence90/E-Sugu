from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'commandes', OrderViewSet, basename='commandes')
router.register(r'my-orders', BuyerOrdersViewSet, basename='my-orders')
router.register(r'seller-orders', SellerOrdersViewSet, basename='seller-orders')

urlpatterns = [
    path('', include(router.urls)),  # IMPORTANT : pas de /api ici !

    path('creer/', CreateOrderView.as_view(), name='creer-commande'),
    path('mes/', OrderViewSet.as_view({'get': 'list'}), name='mes-commandes'),

    path('bulk-action/', BulkOrderActionView.as_view(), name='bulk-action'),
    path('export/', ExportOrdersView.as_view(), name='export-orders'),
    path('stats/', OrderStatsView.as_view(), name='order-stats'),

    # Vendor endpoints
    path('vendor/orders/', VendorOrdersView.as_view(), name='vendor-orders'),
    path('vendor/orders/<int:order_id>/', VendorOrderDetailView.as_view(), name='vendor-order-detail'),
    path('vendor/orders-debug/', vendor_orders_debug, name='vendor-orders-debug'),
    path('vendor/orders/<int:order_id>/update-status/', 
         VendorOrderStatusUpdateView.as_view(), 
         name='vendor-order-update-status'),
    path('stats/', OrderStatsView.as_view(), name='order-stats'),  # Statistiques selon le type d'utilisateur
    path('stats/admin/', AdminOrderStatsView.as_view(), name='admin-order-stats'),  # Statistiques admin seulement
    path('stats/user/', UserOrderStatsView.as_view(), name='user-order-stats'),  # Statistiques utilisateur seulement
    path('stats/admin/dashboard/', AdminDashboardStatsView.as_view(), name='admin-dashboard-stats'),
    path('stats/admin/analytics/', admin_orders_analytics, name='admin-orders-analytics'),
    path('stats/admin/time-series/', admin_time_series_stats, name='admin-time-series-stats'),
    path('stats/admin/performance/', admin_performance_metrics, name='admin-performance-metrics'),
    path('stats/admin/geographic/', admin_geographic_analysis, name='admin-geographic-analysis'),
    path('stats/admin/products/', admin_product_analysis, name='admin-product-analysis'),
    path('stats/admin/alerts/', admin_alerts, name='admin-alerts'),
    path('admin/all/', admin_all_orders, name='admin-all-orders'),
    # Statistiques en temps réel (optionnel - si vous voulez WebSocket)
    path('comprehensive/dashboard', admin_comprehensive_dashboard, name='admin-realtime-stats'),
    path('recent/', admin_recent_orders, name='admin-recent-orders'),
    path('dashboard/recent/', admin_dashboard_recent_orders, name='dashboard-recent-orders'),
    path('urgent/', admin_urgent_orders, name='admin-urgent-orders'),
]
