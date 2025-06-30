# listings/views.py
from rest_framework import viewsets
from rest_framework.permissions import BasePermission, IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .models import Listing, Image
from .serializers import ListingSerializer, ImageUploadSerializer
from categories.models import Category
from django_filters.rest_framework import DjangoFilterBackend
from .filters import ListingFilter
from rest_framework import viewsets, filters

class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.filter(status='active')
    serializer_class = ListingSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ListingFilter
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['price', 'created_at']
    ordering = ['-created_at'] 
    def perform_create(self, serializer):
        category_id = self.request.data.get('category_id')
        try:
            category = Category.objects.get(id=category_id)
            serializer.save(user=self.request.user, category=category)
        except Category.DoesNotExist:
            raise serializer.ValidationError("Catégorie non trouvée")

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get('category')
        price_max = self.request.query_params.get('price_max')
        location = self.request.query_params.get('location')
        if category:
            queryset = queryset.filter(category__name=category)
        if price_max:
            queryset = queryset.filter(price__lte=price_max)
        if location:
            queryset = queryset.filter(location__icontains=location)
        return queryset

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy', 'upload_image']:
            return [IsAuthenticated(), IsOwner()]
        return super().get_permissions()

    @action(detail=True, methods=['post'], url_path='images')
    def upload_image(self, request, pk=None):
        listing = self.get_object()
        serializer = ImageUploadSerializer(data=request.data)
        if serializer.is_valid():
            Image.objects.create(listing=listing, image=serializer.validated_data['image'])
            return Response({'message': 'Image ajoutée'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOwner])
    def mark_as_sold(self, request, pk=None):
        listing = self.get_object()
        listing.mark_as_sold()
        return Response({'message': 'Annonce marquée comme vendue.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOwner])
    def deactivate(self, request, pk=None):
        listing = self.get_object()
        listing.deactivate()
        return Response({'message': 'Annonce désactivée (expirée).'}, status=status.HTTP_200_OK)