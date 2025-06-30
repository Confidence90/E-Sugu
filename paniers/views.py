from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Panier
from .serializers import PanierSerializer
from listings.models import Listing

class PanierViewSet(viewsets.ModelViewSet):
    serializer_class = PanierSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Panier.objects.filter(user=self.request.user).select_related('listing')

    def perform_create(self, serializer):
        listing_id = serializer.validated_data['listing_id']
        quantity = serializer.validated_data['quantity']
        listing = Listing.objects.get(id=listing_id)

        panier_item, _ = Panier.objects.update_or_create(
            user=self.request.user,
            listing=listing,
            defaults={'quantity': quantity}
        )
        serializer.instance = panier_item

class PanierTotalView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        total = sum(p.total_price() for p in Panier.objects.filter(user=request.user))
        return Response({'total_price': total})
