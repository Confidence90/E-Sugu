# administration/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from listings.models import Listing
from events.models import Event
from payments.models import Transaction
from django.db.models import Sum
from users.models import User

class AdminStatsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        total_commission = Transaction.objects.filter(status='completed').aggregate(total=Sum('commission'))['total'] or 0
        total_users = User.objects.count()
        total_listings = Listing.objects.count()
        return Response({
            'total_commission': float(total_commission),
            'total_users': total_users,
            'total_listings': total_listings
        }, status=status.HTTP_200_OK)

class AdminListingDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request, id):
        try:
            listing = Listing.objects.get(id=id)
            listing.delete()
            return Response({'message': 'Annonce supprimée'}, status=status.HTTP_204_NO_CONTENT)
        except Listing.DoesNotExist:
            return Response({'error': 'Annonce non trouvée'}, status=status.HTTP_404_NOT_FOUND)

class AdminEventDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request, id):
        try:
            event = Event.objects.get(id=id)
            event.delete()
            return Response({'message': 'Événement supprimé'}, status=status.HTTP_204_NO_CONTENT)
        except Event.DoesNotExist:
            return Response({'error': 'Événement non trouvé'}, status=status.HTTP_404_NOT_FOUND)