from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, CreateOrderView, BulkOrderActionView, ExportOrdersView, OrderStatsView     

router = DefaultRouter()
router.register('commandes', OrderViewSet, basename='commande')

urlpatterns = router.urls + [
    path('commander/', CreateOrderView.as_view(), name='creer-commande'),
    path('mes-commandes/', OrderViewSet.as_view({'get': 'list'}), name='mes-commandes'),
    path('bulk-action/', BulkOrderActionView.as_view(), name='bulk-action'),
    path('export/', ExportOrdersView.as_view(), name='export-orders'),
    path('stats/', OrderStatsView.as_view(), name='order-stats'),
    
]
