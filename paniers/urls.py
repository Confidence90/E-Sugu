from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PanierViewSet, PanierTotalView

router = DefaultRouter()
router.register('panier', PanierViewSet, basename='panier')

urlpatterns = [
    path('', include(router.urls)),
    path('panier/total/', PanierTotalView.as_view(), name='panier-total'),
    path('panier/validate/', PanierViewSet.as_view({'get': 'validate'}), name='panier-validate'),
    path('panier/clear/', PanierViewSet.as_view({'post': 'clear'}), name='panier-clear'),
]