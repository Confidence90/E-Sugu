from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Sum
from django.shortcuts import get_object_or_404

from users.models import User
from listings.models import Listing
from events.models import Event
from payments.models import Transaction
from .models import AdminLog
from .serializers import AdminLogSerializer

# KYC Approval
class KYCApproveView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        if not request.user.is_staff:
            return Response({'error': 'Accès admin requis.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response({'error': 'Utilisateur non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        user.is_seller_pending = False
        user.is_seller = True
        user.save()

        AdminLog.objects.create(
            admin=request.user,
            action='KYC Approved',
            details=f'KYC approuvé pour {user.username}'
        )

        return Response({'message': 'KYC approuvé'}, status=status.HTTP_200_OK)

# Statistiques
class AdminStatsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        total_commission = Transaction.objects.filter(status='completed').aggregate(total=Sum('commission'))['total'] or 0
        total_users = User.objects.count()
        total_listings = Listing.objects.count()
        total_events = Event.objects.count()

        return Response({
            'total_commission': float(total_commission),
            'total_users': total_users,
            'total_listings': total_listings,
            'total_events': total_events
        }, status=status.HTTP_200_OK)

# Suppression d’annonce avec log
class AdminListingDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request, id):
        listing = get_object_or_404(Listing, id=id)
        AdminLog.objects.create(
            admin=request.user,
            action='Suppression annonce',
            details=f"Annonce supprimée : {listing.title}"
        )
        listing.delete()
        return Response({'message': 'Annonce supprimée'}, status=status.HTTP_204_NO_CONTENT)

# Suppression d’événement avec log
class AdminEventDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request, id):
        event = get_object_or_404(Event, id=id)
        AdminLog.objects.create(
            admin=request.user,
            action='Suppression événement',
            details=f"Événement supprimé : {event.title}"
        )
        event.delete()
        return Response({'message': 'Événement supprimé'}, status=status.HTTP_204_NO_CONTENT)

# Liste des journaux admin
class AdminLogListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        logs = AdminLog.objects.all().order_by('-created_at')
        serializer = AdminLogSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
