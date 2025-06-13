# payments/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import time  # <-- Ajout de l'import manquant
from django.conf import settings
from .models import Transaction
from listings.models import Listing
from .serializers import TransactionSerializer, CreateTransactionSerializer

class TransactionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateTransactionSerializer(data=request.data)
        if serializer.is_valid():
            listing_id = serializer.validated_data['listing_id']
            payment_method = serializer.validated_data['payment_method']
            
            try:
                listing = Listing.objects.get(id=listing_id, status='active')
                amount = listing.price
                commission = amount * (7 / 100)
                net_amount = amount - commission
                
                payment_response = self.process_mobile_payment(
                    payment_method,
                    amount,
                    request.user.phone_number,
                    listing_id
                )
                
                if payment_response['success']:
                    transaction = Transaction.objects.create(
                        listing=listing,
                        buyer=request.user,
                        seller=listing.user,
                        amount=amount,
                        commission=commission,
                        net_amount=net_amount,
                        status='pending',
                        payment_method=payment_method,
                        payment_reference=payment_response['reference']
                    )
                    
                    listing.status = 'sold'
                    listing.save()
                    
                    return Response({
                        'status': 'pending',
                        'transaction_id': transaction.id,
                        'payment_reference': payment_response['reference']
                    }, status=status.HTTP_201_CREATED)
                else:
                    return Response({
                        'error': payment_response['message']
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except Listing.DoesNotExist:
                return Response({'error': 'Annonce non trouvée'}, status=status.HTTP_404_NOT_FOUND)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        transactions = Transaction.objects.filter(buyer=request.user) | Transaction.objects.filter(seller=request.user)
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def process_mobile_payment(self, payment_method, amount, phone_number, listing_id):
        """
        Méthode à implémenter pour Orange Money et Moov Money
        """
        if payment_method == 'orange_money':
            return {
                'success': True,
                'reference': f"OM_{listing_id}_{int(time.time())}",  # <-- Utilisation de time
                'message': 'Paiement Orange Money initié'
            }
        elif payment_method == 'moov_money':
            return {
                'success': True,
                'reference': f"MOOV_{listing_id}_{int(time.time())}",  # <-- Utilisation de time
                'message': 'Paiement Moov Money initié'
            }
        else:
            return {
                'success': False,
                'message': 'Méthode de paiement non supportée'
            }

class TransactionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            transaction = Transaction.objects.get(id=id)
            if transaction.buyer == request.user or transaction.seller == request.user:
                serializer = TransactionSerializer(transaction)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response({'error': 'Non autorisé'}, status=status.HTTP_403_FORBIDDEN)
        except Transaction.DoesNotExist:
            return Response({'error': 'Transaction non trouvée'}, status=status.HTTP_404_NOT_FOUND)

class RefundView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        try:
            transaction = Transaction.objects.get(id=id)

            if request.user != transaction.buyer and request.user != transaction.seller:
                return Response({'error': 'Non autorisé'}, status=status.HTTP_403_FORBIDDEN)

            if transaction.status != 'pending':
                return Response({'error': 'La transaction ne peut pas être remboursée'}, status=status.HTTP_400_BAD_REQUEST)

            # Exemple de traitement fictif du remboursement
            transaction.status = 'refunded'
            transaction.save()

            # Optionnel : changer le statut de l'annonce à nouveau disponible
            listing = transaction.listing
            listing.status = 'active'
            listing.save()

            return Response({
                'status': 'refunded',
                'message': f'Transaction {transaction.id} remboursée avec succès'
            }, status=status.HTTP_200_OK)

        except Transaction.DoesNotExist:
            return Response({'error': 'Transaction non trouvée'}, status=status.HTTP_404_NOT_FOUND)
