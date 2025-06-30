import stripe
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Transaction, Revenue
from .serializers import TransactionSerializer, RevenueSerializer
from commandes.models import Order

stripe.api_key = "your_stripe_secret_key"

class PaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id = request.data.get('order_id')
        order = Order.objects.get(id=order_id, user=request.user)
        try:
            charge = stripe.Charge.create(
                amount=int(order.total_price * 100),
                currency='usd',
                source=request.data.get('stripe_token'),
                description='Charge for order #' + str(order_id)
            )
            transaction = Transaction.objects.create(order=order, stripe_transaction_id=charge.id, amount=order.total_price, status='success')
            revenue = Revenue.objects.create(transaction=transaction, seller=order.listing.user, amount=order.total_price * 0.9)  # 10% commission
            order.status = 'completed'
            order.save()
            return Response({'message': 'Payment successful'}, status=status.HTTP_200_OK)
        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class RevenueListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        revenues = Revenue.objects.filter(seller=request.user)
        serializer = RevenueSerializer(revenues, many=True)
        return Response(serializer.data)