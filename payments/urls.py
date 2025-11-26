from django.urls import path
from .views import *

urlpatterns = [
    path('', TransactionView.as_view(), name='transactions'),
    path('summary/', PaymentSummaryView.as_view(), name='payment-summary'), 
    path('<int:id>/', TransactionDetailView.as_view(), name='transaction-detail'),
    path('<int:id>/refund/', RefundView.as_view(), name='refund'),
    path('confirm/', PaymentConfirmationView.as_view(), name='confirm-payment'),
    path('clear-cart/', ClearCartAfterPaymentView.as_view(), name='clear-cart'),  # Nouvelle route
   
]