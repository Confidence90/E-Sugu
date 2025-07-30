# listings/views.py
from rest_framework import viewsets
from rest_framework.permissions import BasePermission, IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .models import Listing, Image
from rest_framework.exceptions import ValidationError

from .serializers import ListingSerializer, ImageUploadSerializer, ListingCreateSerializer
from categories.models import Category
from django_filters.rest_framework import DjangoFilterBackend
from .filters import ListingFilter
from rest_framework import viewsets, filters
from rest_framework.pagination import PageNumberPagination
import random

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 40
    page_size_query_param = 'page_size'
    max_page_size = 100

class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.filter(status='active')
    serializer_class = ListingSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ListingFilter
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['price', 'created_at']
    ordering = ['-created_at'] 

    def get_serializer_class(self):
        if self.action == 'create':
            return ListingCreateSerializer
        return ListingSerializer



    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'featured':
            return queryset.filter(is_featured=True).order_by('?')
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

    @action(detail=False, methods=['get'])
    def featured(self, request):
        queryset = self.get_queryset().filter(is_featured=True).order_by('?')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    