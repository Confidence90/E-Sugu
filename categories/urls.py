from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet,
    CategoryDetailWithChildrenAPIView,
    CategoryByNameAPIView  # 👈 Assure-toi qu'elle est importée
)

router = DefaultRouter()
router.register(r'', CategoryViewSet, basename='category')

urlpatterns = [
    # 🔥 Cette route DOIT être avant le include(router)
    path('categories/<str:name>/', CategoryByNameAPIView.as_view(), name='category-by-name'),

    # Autres routes personnalisées
    path('categories/<int:pk>/with-children/', CategoryDetailWithChildrenAPIView.as_view(), name='category-with-children'),

    # Routes du ViewSet
    path('', include(router.urls)),
]
