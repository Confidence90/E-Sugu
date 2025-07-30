from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, CategoryDetailWithChildrenAPIView

# Créer un routeur pour les routes automatiques du ViewSet
router = DefaultRouter()
router.register(r'', CategoryViewSet, basename='category')

# Définir les URL
urlpatterns = [
    path('', include(router.urls)),

    # Endpoint personnalisé pour récupérer une catégorie avec ses enfants
    path('categories/<int:pk>/with-children/', CategoryDetailWithChildrenAPIView.as_view(), name='category-with-children'),
]
