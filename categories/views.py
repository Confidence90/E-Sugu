# categories/views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from .models import Category
from rest_framework import generics
from rest_framework.decorators import action
from .serializers import CategorySerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    def get_queryset(self):
        # On ne retourne que les catégories principales (sans parent)
        return Category.objects.filter(parent__isnull=True)
    @action(detail=False, methods=['get'], url_path='subcategories')
    def subcategories(self, request):
        subcats = Category.objects.filter(parent__isnull=False)
        serializer = self.get_serializer(subcats, many=True)
        return Response(serializer.data)

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminUser()]
        return super().get_permissions()
class CategoryDetailWithChildrenAPIView(generics.RetrieveAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]