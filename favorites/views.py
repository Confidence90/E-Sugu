# favorites/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import FavoriteListing, FavoriteEvent
from .serializers import FavoriteListingSerializer, FavoriteEventSerializer
from listings.models import Listing
from events.models import Event

class FavoriteListingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FavoriteListingSerializer(data=request.data)
        if serializer.is_valid():
            listing_id = serializer.validated_data['listing_id']
            try:
                listing = Listing.objects.get(id=listing_id)
                FavoriteListing.objects.create(user=request.user, listing=listing)
                return Response({'message': 'Annonce ajoutée aux favoris'}, status=status.HTTP_201_CREATED)
            except Listing.DoesNotExist:
                return Response({'error': 'Annonce non trouvée'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FavoriteEventView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FavoriteEventSerializer(data=request.data)
        if serializer.is_valid():
            event_id = serializer.validated_data['event_id']
            try:
                event = Event.objects.get(id=event_id)
                FavoriteEvent.objects.create(user=request.user, event=event)
                return Response({'message': 'Événement ajouté aux favoris'}, status=status.HTTP_201_CREATED)
            except Event.DoesNotExist:
                return Response({'error': 'Événement non trouvé'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FavoriteListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        favorite_listings = FavoriteListing.objects.filter(user=request.user)
        favorite_events = FavoriteEvent.objects.filter(user=request.user)
        listing_serializer = FavoriteListingSerializer(favorite_listings, many=True)
        event_serializer = FavoriteEventSerializer(favorite_events, many=True)
        return Response({
            'listings': listing_serializer.data,
            'events': event_serializer.data
        }, status=status.HTTP_200_OK)

class FavoriteDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, id):
        try:
            favorite = FavoriteListing.objects.get(id=id, user=request.user)
            favorite.delete()
            return Response({'message': 'Favori supprimé'}, status=status.HTTP_204_NO_CONTENT)
        except FavoriteListing.DoesNotExist:
            try:
                favorite = FavoriteEvent.objects.get(id=id, user=request.user)
                favorite.delete()
                return Response({'message': 'Favori supprimé'}, status=status.HTTP_204_NO_CONTENT)
            except FavoriteEvent.DoesNotExist:
                return Response({'error': 'Favori non trouvé'}, status=status.HTTP_404_NOT_FOUND)