# reviews/urls.py
from django.urls import path
from .views import ReviewView, ReviewDetailView

urlpatterns = [
    path('', ReviewView.as_view(), name='reviews'),
    path('<int:id>/', ReviewDetailView.as_view(), name='review-detail'),
]