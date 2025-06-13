# payments/urls.py
from django.urls import path
from .views import TransactionView, TransactionDetailView, RefundView

urlpatterns = [
    path('', TransactionView.as_view(), name='transactions'),
    path('<int:id>/', TransactionDetailView.as_view(), name='transaction-detail'),
    path('<int:id>/refund/', RefundView.as_view(), name='refund'),
]