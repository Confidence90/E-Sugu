from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import FavoriteListing, FavoriteEvent
from .serializers import FavoriteListingSerializer, FavoriteEventSerializer
from listings.models import Listing
from events.models import Event

# ---------- FAVORIS D’ANNONCES ----------
class FavoriteListingListView(generics.ListAPIView):
    serializer_class = FavoriteListingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FavoriteListing.objects.filter(user=self.request.user)


class AddFavoriteListingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FavoriteListingSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            listing_id = serializer.validated_data['listing_id']
            listing = Listing.objects.get(id=listing_id)

            # Vérifie si déjà dans les favoris
            if FavoriteListing.objects.filter(user=request.user, listing=listing).exists():
                return Response({'detail': 'Cette annonce est déjà dans vos favoris.'}, status=status.HTTP_200_OK)

            FavoriteListing.objects.create(user=request.user, listing=listing)
            return Response({'detail': 'Annonce ajoutée aux favoris.'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RemoveFavoriteListingView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, listing_id):
        try:
            favorite = FavoriteListing.objects.get(user=request.user, listing_id=listing_id)
            favorite.delete()
            return Response({'detail': 'Annonce retirée des favoris.'}, status=status.HTTP_204_NO_CONTENT)
        except FavoriteListing.DoesNotExist:
            return Response({'error': 'Cette annonce n’est pas dans vos favoris.'}, status=status.HTTP_404_NOT_FOUND)


# ---------- FAVORIS D’ÉVÉNEMENTS ----------
class FavoriteEventListView(generics.ListAPIView):
    serializer_class = FavoriteEventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FavoriteEvent.objects.filter(user=self.request.user)


class AddFavoriteEventView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FavoriteEventSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            event_id = serializer.validated_data['event_id']
            event = Event.objects.get(id=event_id)

            if FavoriteEvent.objects.filter(user=request.user, event=event).exists():
                return Response({'detail': 'Cet événement est déjà dans vos favoris.'}, status=status.HTTP_200_OK)

            FavoriteEvent.objects.create(user=request.user, event=event)
            return Response({'detail': 'Événement ajouté aux favoris.'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RemoveFavoriteEventView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, event_id):
        try:
            favorite = FavoriteEvent.objects.get(user=request.user, event_id=event_id)
            favorite.delete()
            return Response({'detail': 'Événement retiré des favoris.'}, status=status.HTTP_204_NO_CONTENT)
        except FavoriteEvent.DoesNotExist:
            return Response({'error': 'Cet événement n’est pas dans vos favoris.'}, status=status.HTTP_404_NOT_FOUND)
