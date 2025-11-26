# ⚠️ NOTES IMPORTANTES

    Panier unique par utilisateur : Chaque utilisateur a un seul panier

    Stock en temps réel : Les validations utilisent le stock actuel

    Auto-création : Le panier est créé automatiquement au premier ajout

    Prix dynamique : Les totaux sont calculés en temps réel

    Sécurité : Impossible de modifier le panier d'un autre utilisateur

# 🔄 INTÉGRATION AVEC COMMANDES

Le panier est conçu pour être une étape intermédiaire avant la création de commandes. Une fois validé via /panier/validate/, le panier peut être transformé en commande via l'API des commandes.

Workflow recommandé :

    ✅ Ajouter articles au panier

    ✅ Valider le panier (/panier/validate/)

    ✅ Créer commande depuis le panier validé

    ✅ Vider le panier après commande créée


#   📋 Documentation des URLs Panier
*🌐 URLs Disponibles pour le Panier d'Achat*
/api/paniers/
*🔐 ENDPOINTS AUTHENTIFIÉS (IsAuthenticated)*
# Tous les endpoints du panier nécessitent une authentification
*🛒 GESTION DU PANIER*
*Voir son panier*
GET /api/paniers/panier/
Description : Récupère le panier complet de l'utilisateur avec tous les articles
Réponse :
json

{
  "id": 1,
  "user": 1,
  "items": [
    {
      "id": 1,
      "listing": {
        "id": 1,
        "title": "iPhone 13",
        "price": 800.00
      },
      "quantity": 2,
      "total_price": 1600.00
    }
  ],
  "total_price": 1600.00,
  "item_count": 1
}

*Ajouter un article au panier
POST /api/paniers/panier/
Description : Ajoute un produit au panier avec validation de stock
Body :
json

{
  "listing_id": 1,
  "quantity": 2
}

Validations :

    Vérifie la disponibilité du stock

    Si quantité > stock disponible : ajuste automatiquement

    Si article déjà présent : ajoute la quantité

*Modifier la quantité d'un article*
PUT /api/paniers/panier/{item_id}/
Description : Modifie la quantité d'un article spécifique dans le panier
Body :
json

{
  "quantity": 3
}

Comportement :

    Si quantity = 0 : supprime l'article

    Si quantity > stock : retourne erreur

    Met à jour la quantité

*Supprimer un article du panier*
DELETE /api/paniers/panier/{item_id}/
Description : Supprime un article spécifique du panier
Réponse :
json

{
  "message": "Article supprimé du panier"
}

**🎯 ACTIONS SPÉCIALES DU PANIER**
*Vider tout le panier*
POST /api/paniers/panier/clear/
Description : Supprime tous les articles du panier
Réponse :
json

{
  "message": "3 article(s) supprimé(s) du panier"
}

*Valider le panier*
GET /api/paniers/panier/validate/
Description : Vérifie si le panier peut être transformé en commande
Réponse :
json

{
  "can_create_order": true,
  "message": "Panier valide",
  "total_items": 2,
  "total_price": 1200.50
}

Vérifications effectuées :

    Panier non vide

    Tous les produits en stock

    Quantités valides

*Obtenir le total du panier*
GET /api/paniers/panier/total/
Description : Récupère le prix total et les infos de validation
Réponse :
json

{
  "total_price": 1600.00,
  "item_count": 2,
  "can_create_order": true,
  "validation_message": "Panier valide",
  "message": "Panier avec 2 article(s)"
}

#   📊 RÉSUMÉ COMPLET DES ENDPOINTS
*Méthode	URL	Description*
GET	/panier/	Voir le panier complet
POST	/panier/	Ajouter un article
PUT	/panier/{item_id}/	Modifier quantité
DELETE	/panier/{item_id}/	Supprimer un article
POST	/panier/clear/	Vider tout le panier
GET	/panier/validate/	Valider le panier
GET	/panier/total/	Total et infos validation
