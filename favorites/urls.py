# favorites/urls.py
from django.urls import path
from .views import FavoriteListingView, FavoriteEventView, FavoriteListView, FavoriteDeleteView

urlpatterns = [
    path('listings/', FavoriteListingView.as_view(), name='favorite-listing'),
    path('events/', FavoriteEventView.as_view(), name='favorite-event'),
    path('', FavoriteListView.as_view(), name='favorite-list'),
    path('<int:id>/', FavoriteDeleteView.as_view(), name='favorite-delete'),
]