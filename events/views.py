# events/views.py
from rest_framework import viewsets
from rest_framework.permissions import BasePermission, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .models import Event, EventListing, EventMessage
from listings.models import Listing
from .serializers import EventSerializer, CreateEventSerializer, EventMessageSerializer, CreateEventMessageSerializer

class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        listing_ids = self.request.data.get('listing_ids', [])
        special_offer = self.request.data.get('special_offer')
        event = serializer.save(user=self.request.user)
        for listing_id in listing_ids:
            try:
                listing = Listing.objects.get(id=listing_id, user=self.request.user)
                EventListing.objects.create(event=event, listing=listing, special_offer=special_offer)
            except Listing.DoesNotExist:
                pass

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateEventSerializer
        return EventSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy', 'create_chat_message', 'get_chat_messages']:
            return [IsAuthenticated(), IsOwner()]
        return super().get_permissions()

    @action(detail=True, methods=['post'], url_path='chat')
    def create_chat_message(self, request, pk=None):
        event = self.get_object()
        serializer = CreateEventMessageSerializer(data=request.data)
        if serializer.is_valid():
            message = serializer.save(event=event, sender=request.user)
            return Response(EventMessageSerializer(message).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='chat')
    def get_chat_messages(self, request, pk=None):
        event = self.get_object()
        messages = event.chat_messages.all()
        serializer = EventMessageSerializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)