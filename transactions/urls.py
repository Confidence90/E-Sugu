from django.urls import path
from .views import PaymentView, RevenueListView

urlpatterns = [
    path('pay/', PaymentView.as_view(), name='payment'),
    path('revenues/', RevenueListView.as_view(), name='revenue_list'),
]