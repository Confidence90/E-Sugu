from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PanierViewSet, PanierTotalView

router = DefaultRouter()
router.register('panier', PanierViewSet, basename='panier')

urlpatterns = router.urls + [
    path('panier/total/', PanierTotalView.as_view(), name='panier-total'),
]
