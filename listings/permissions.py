# permissions.py - NOUVEAU FICHIER
from rest_framework import permissions

class IsSellerPermission(permissions.BasePermission):
    """
    Permission personnalisée pour vérifier qu'un utilisateur est un vendeur actif
    """
    message = "Seuls les vendeurs vérifiés peuvent publier des annonces."

    def has_permission(self, request, view):
        # Vérifier l'authentification d'abord
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Vérifier le rôle et le statut
        return (
            request.user.role == 'seller' and 
            request.user.is_seller and 
            not request.user.is_seller_pending
        )