from django.urls import path
from .views import (
    FavoriteListingListView,
    AddFavoriteListingView,
    RemoveFavoriteListingView,
    FavoriteEventListView,
    AddFavoriteEventView,
    RemoveFavoriteEventView,
)

urlpatterns = [
    # --- Annonces ---
    path('listings/', FavoriteListingListView.as_view(), name='favorite-listings'),               # GET : liste des annonces favorites
    path('listings/add/', AddFavoriteListingView.as_view(), name='add-favorite-listing'),         # POST : ajouter une annonce aux favoris
    path('listings/remove/<int:listing_id>/', RemoveFavoriteListingView.as_view(), name='remove-favorite-listing'),  # DELETE

    # --- Événements ---
    path('events/', FavoriteEventListView.as_view(), name='favorite-events'),                      # GET : liste des événements favoris
    path('events/add/', AddFavoriteEventView.as_view(), name='add-favorite-event'),                # POST : ajouter un événement aux favoris
    path('events/remove/<int:event_id>/', RemoveFavoriteEventView.as_view(), name='remove-favorite-event'),  # DELETE
]
