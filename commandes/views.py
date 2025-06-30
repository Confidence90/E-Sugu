from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Order, OrderItem
from .serializers import OrderSerializer
from paniers.models import Panier  # ton modèle de panier renommé
from listings.models import Listing

class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

class CreateOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        panier_items = Panier.objects.filter(user=user)

        if not panier_items.exists():
            return Response({'error': 'Ton panier est vide.'}, status=status.HTTP_400_BAD_REQUEST)

        order = Order.objects.create(user=user)
        total = 0

        for item in panier_items:
            price = item.listing.price
            quantity = item.quantity
            total += price * quantity
            OrderItem.objects.create(
                order=order,
                listing=item.listing,
                quantity=quantity,
                price=price,
            )
        
        order.total_price = total
        order.save()

        panier_items.delete()  # vider le panier après commande

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
