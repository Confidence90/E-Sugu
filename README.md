### URLs d'accès
- **API Base**: `http://localhost:3000`
- **Interface Web**: `http://localhost:3000` (pour visualiser les données)

# 🔐 AUTHENTIFICATION & UTILISATEUR
- **Inscription & Connexion**

   POST '/api/users/register/ - Créer un compte'

    POST /api/users/verify-otp/ - Vérifier OTP

    POST /api/users/login/ - Connexion

    POST /api/users/logout/ - Déconnexion

    POST /api/users/refresh-token/ - Rafraîchir token

    POST /api/users/resend-otp/ - Renvoyer OTP

Mot de passe

    POST /api/users/password-reset/ - Demander réinitialisation

    POST /api/users/password-reset/confirm/ - Confirmer avec OTP

    GET /api/users/password-reset-confirm/<uidb64>/<token>/ - Valider lien

    PATCH /api/users/set-new-password/ - Définir nouveau mot de passe

Profil utilisateur

    GET /api/users/profile/ - Voir son profil

    PUT /api/users/profile/ - Modifier son profil

    GET /api/users/me/ - Tester l'authentification

# 🔑 VÉRIFICATION ADMIN/STAFF
- **URLs spécifiques pour vérifier les permissions**
    GET /api/users/check-admin-permission/

{
  "is_admin": true/false,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role": "admin",
    "is_staff": true,
    "is_superuser": true,
    "is_active": true
  }
}

# Dashboard Admin (nécessite permissions admin)

GET /api/users/admin/dashboard/stats/
GET /api/users/admin/dashboard/recent-orders/
GET /api/users/admin/dashboard/top-vendors/

# Gestion des utilisateurs (Admin seulement)

GET /api/users/admin/users/ - Lister les utilisateurs
GET /api/users/admin/stats/ - Statistiques utilisateurs
PATCH /api/users/admin/users/{id}/ - Modifier un utilisateur

# 👨‍💼 VENDOR/PROFIL VENDEUR

- **Profil vendeur**
GET /api/users/vendor/profile/ - Voir profil vendeur
POST /api/users/vendor/profile/ - Créer/mettre à jour profil
PUT /api/users/vendor/profile/ - Mettre à jour complètement
PATCH /api/users/vendor/profile/ - Mettre à jour partiellement

- **Statut vendeur**

GET /api/users/vendor/check-status/ - Vérifier statut vendeur
POST /api/users/vendor/activate/ - Activer statut vendeur
POST /api/users/vendor/create-profile/ - Créer profil vendeur
GET /api/users/vendor/check-setup/ - Vérifier setup vendeur

- **Statistiques vendeur**

GET /api/users/vendor/stats/ - Statistiques complètes
GET /api/users/vendor/sales-report/ - Rapport de ventes
GET /api/users/vendor/performance/ - Performance détaillée
GET /api/users/vendor/quick-stats/ - Statistiques rapides

# 🌐 AUTHENTIFICATION SOCIALE

POST /api/users/google/login/ - Connexion Google
GET /api/users/google/callback/ - Callback Google
POST /api/users/facebook/login/ - Connexion Facebook
POST /api/users/apple/login/ - Connexion Apple

# 📍 ADDRESSES

GET /api/users/addresses/ - Lister adresses
POST /api/users/addresses/ - Créer adresse
GET /api/users/addresses/{id}/ - Voir adresse
PUT /api/users/addresses/{id}/ - Modifier adresse
PATCH /api/users/addresses/{id}/ - Modifier partiellement
DELETE /api/users/addresses/{id}/ - Supprimer adresse
POST /api/users/addresses/{id}/set-default/ - Définir par défaut

# 🎯 UTILITAIRES & DÉBOGAGE

GET /api/users/regions/ - Liste des régions
GET /api/users/check-listing-permission/ - Vérifier permission annonces
GET /api/users/vendor/debug-user-info/ - Debug info utilisateur
GET /api/users/vendor/debug-visitors/ - Debug statistiques visiteurs
POST /api/users/track-dashboard-view/ - Tracker vue dashboard

# 🛠️ ADMIN AVANCÉ (ViewSet)

- **Le ViewSet AdminUserViewSet offre ces endpoints :**

GET /api/users/admin/users/ - Lister utilisateurs
POST /api/users/admin/users/ - Créer utilisateur
GET /api/users/admin/users/{id}/ - Voir utilisateur
PUT /api/users/admin/users/{id}/ - Modifier utilisateur
PATCH /api/users/admin/users/{id}/ - Modifier partiellement
DELETE /api/users/admin/users/{id}/ - Supprimer utilisateur

# Actions custom
GET /api/users/admin/users/stats/ - Statistiques
POST /api/users/admin/users/{id}/reset_password/ - Reset password
GET /api/users/admin/users/export/ - Export CSV

# 📋 RÉSUMÉ DES MÉTHODES PAR CATÉGORIE

- **Authentification Basique**

    POST register, login, logout, verify-otp, refresh-token

    PATCH set-new-password

**Vérification Permissions**

    GET check-admin-permission, check-listing-permission, me

**Administration**

    GET admin/dashboard/stats, admin/users/, admin/stats/

    PATCH admin/users/{id}/

    GET admin/dashboard/recent-orders, admin/dashboard/top-vendors

**Vendeur**

    GET/POST/PUT/PATCH vendor/profile/

    GET vendor/stats, vendor/performance, vendor/quick-stats

    POST vendor/activate, vendor/create-profile

**Social & Utilitaires**

    POST google/login, facebook/login, apple/login

    GET regions, addresses/

# 🌐 URLs Disponibles pour les Catégories

**Base URL**
/api/categories/

**📖 ENDPOINTS PUBLIC (AllowAny)**
*Lister toutes les catégories principales*
GET /api/categories/
Description : Récupère toutes les catégories principales (sans parent)
Réponse : Liste des catégories principales

*Récupérer une catégorie par ID*
GET /api/categories/{id}/
Description : Récupère les détails d'une catégorie spécifique par son ID
Paramètres : id (integer) - ID de la catégorie

*Récupérer une catégorie par nom*
GET /api/categories/{name}/
Description : Récupère une catégorie par son nom (insensible à la casse)
Paramètres : name (string) - Nom de la catégorie
Exemple : /api/categories/electronique/

*Récupérer une catégorie avec ses enfants*
GET /api/categories/{pk}/with-children/
Description : Récupère une catégorie avec tous ses sous-catégories
Paramètres : pk (integer) - ID de la catégorie parente

*Lister toutes les sous-catégories*
GET /api/categories/subcategories/
Description : Récupère toutes les sous-catégories (avec parent)
Réponse : Liste de toutes les catégories enfants

#   🔐 ENDPOINTS ADMIN SEULEMENT (IsAuthenticated + IsAdminUser)
**Créer une nouvelle catégorie**
POST /api/categories/
Permissions : Admin seulement
Body :
{
  "name": "Nom de la catégorie",
  "description": "Description optionnelle",
  "parent": null ou ID de la catégorie parente
}
*Modifier complètement une catégorie*
PUT /api/categories/{id}/
Permissions : Admin seulement
Description : Met à jour tous les champs de la catégorie

*Modifier partiellement une catégorie*
PATCH /api/categories/{id}/
Permissions : Admin seulement
Description : Met à jour seulement les champs fournis

*Supprimer une catégorie*
DELETE /api/categories/{id}/
Permissions : Admin seulement
Description : Supprime définitivement la catégorie

# 📊 RÉSUMÉ DES MÉTHODES HTTP
Méthode	URL	Permissions	Description
GET	/api/categories/	Public	Liste catégories principales
GET	/api/categories/{id}/	Public	Détails catégorie par ID
GET	/api/categories/{name}/	Public	Catégorie par nom
GET	/api/categories/{pk}/with-children/	Public	Catégorie avec enfants
GET	/api/categories/subcategories/	Public	Toutes les sous-catégories
POST	/api/categories/	Admin seulement	Créer nouvelle catégorie
PUT	/api/categories/{id}/	Admin seulement	Modifier complètement
PATCH	/api/categories/{id}/	Admin seulement	Modifier partiellement
DELETE	/api/categories/{id}/	Admin seulement	Supprimer catégorie

#   ⚠️ NOTES IMPORTANTES

    Permissions automatiques : Les endpoints de lecture sont publics, les endpoints d'écriture nécessitent un compte admin

    Filtrage automatique : /api/categories/ retourne seulement les catégories principales

    Recherche insensible à la casse : La recherche par nom ignore la casse

    Structure hiérarchique : Utilisez with-children pour obtenir l'arborescence complète

#   🔗 SÉRIALIZEUR UTILISÉ

**Tous les endpoints utilisent le CategorySerializer qui inclut :**

    id - Identifiant unique

    name - Nom de la catégorie

    description - Description optionnelle

    parent - Catégorie parente (si sous-catégorie)

    children - Sous-catégories (si catégorie parente)

Cette documentation couvre l'intégralité des endpoints disponibles pour le module categories.

# 🌐 URLs Disponibles pour les Annonces (Listings)
*Base URL*
/api/listings/

**📖 ENDPOINTS PUBLIC (AllowAny)**
*Lister toutes les annonces actives*
GET /api/listings/listings/
Description : Récupère toutes les annonces actives avec pagination
Filtres disponibles :

    category : Filtrer par nom de catégorie (inclut sous-catégories)

    search : Recherche dans titre, description, location

    ordering : Trier par price, -price, created_at, -created_at

    page : Pagination

    page_size : Taille de page (max 100)

*Récupérer une annonce par ID*
GET /api/listings/listings/{id}/
Description : Détails complets d'une annonce spécifique

*Annonces en vedette*
GET /api/listings/listings/featured/
Description : Annonces marquées comme featured (aléatoire)

*Détails d'une annonce (alternative)*
GET /api/listings/listings/{id}/details/
Description : Endpoint alternatif pour les détails

*Tracker une vue sur une annonce*
POST /api/listings/listings/{listing_id}/track-view/
Description : Enregistre une vue sur une annonce (IP/session tracking)
Permissions : Public

*Test du tracking*
GET /api/listings/listings/{listing_id}/test-tracking/
Description : Endpoint de test pour le système de tracking

**🔐 ENDPOINTS AUTHENTIFIÉS (IsAuthenticated)**
*Créer une nouvelle annonce*
POST /api/listings/listings/
Permissions : Vendeurs vérifiés seulement
Body : Utilise ListingCreateSerializer
json

{
  "title": "Titre de l'annonce",
  "description": "Description détaillée",
  "price": 100.50,
  "category": 1,
  "quantity": 10,
  "location": "Bamako"
}

*Modifier son annonce*
PUT /api/listings/listings/{id}/
PATCH /api/listings/listings/{id}/
Permissions : Propriétaire seulement
Description : Modification complète ou partielle

*Supprimer son annonce*
DELETE /api/listings/listings/{id}/
Permissions : Propriétaire seulement

*Uploader une image*
POST /api/listings/listings/{id}/images/
Permissions : Propriétaire seulement
Body : Form-data avec fichier image
json

{
  "image": [file]
}

*Mes annonces*
GET /api/listings/listings/?my_listings=true
Description : Filtrer pour voir seulement ses propres annonces

**🛒 GESTION DES COMMANDES**
*Créer une commande sur une annonce*
POST /api/listings/listings/{id}/create_order/
Permissions : Authentifié (sauf propriétaire)
Body : OrderCreateSerializer
json

{
  "quantity": 2,
  "shipping_address": "Adresse de livraison",
  "notes": "Notes optionnelles"
}

*Réapprovisionner une annonce*
POST /api/listings/listings/{id}/restock/
Permissions : Propriétaire seulement
Body :
json

{
  "quantity": 50
}

*Marquer comme vendu*
POST /api/listings/listings/{id}/mark_as_sold/
Permissions : Propriétaire seulement

*Désactiver une annonce*
POST /api/listings/listings/{id}/deactivate/
Permissions : Propriétaire seulement

**📦 GESTION DES COMMANDES (OrderViewSet)**
*Lister mes commandes/ventes*
GET /api/listings/orders/
Description : Commandes où l'utilisateur est acheteur OU vendeur

*Détails d'une commande*
GET /api/listings/orders/{id}/
Permissions : Acheteur ou vendeur de la commande

*Confirmer une commande (vendeur)*
POST /api/listings/orders/{id}/confirm/
Permissions : Vendeur seulement

*Annuler une commande*
POST /api/listings/orders/{id}/cancel/
Permissions : Acheteur ou vendeur

# 📊 RÉSUMÉ DES MÉTHODES HTTP

**Listings**
*Méthode	URL	Permissions	Description*
GET	/listings/	Public	Liste annonces actives
GET	/listings/{id}/	Public	Détails annonce
GET	/listings/featured/	Public	Annonces featured
POST	/listings/	Vendeur	Créer annonce
PUT/PATCH	/listings/{id}/	Propriétaire	Modifier annonce
DELETE	/listings/{id}/	Propriétaire	Supprimer annonce
POST	/listings/{id}/images/	Propriétaire	Upload image
POST	/listings/{id}/create_order/	Acheteur	Créer commande
POST	/listings/{id}/restock/	Propriétaire	Réapprovisionner
POST	/listings/{id}/mark_as_sold/	Propriétaire	Marquer vendu
POST	/listings/{id}/deactivate/	Propriétaire	Désactiver
Orders
Méthode	URL	Permissions	Description
GET	/orders/	Authentifié	Mes commandes/ventes
GET	/orders/{id}/	Partie prenante	Détails commande
POST	/orders/{id}/confirm/	Vendeur	Confirmer commande
POST	/orders/{id}/cancel/	Partie prenante	Annuler commande
Tracking
Méthode	URL	Permissions	Description
POST	/listings/{id}/track-view/	Public	Tracker vue
GET	/listings/{id}/test-tracking/	Public	Test tracking

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

#   🌐 URLs Disponibles pour les Paiements
*Base URL*
/api/payments/

*🔐 ENDPOINTS AUTHENTIFIÉS (IsAuthenticated)*

Tous les endpoints de paiement nécessitent une authentification
**💳 GESTION DES PAIEMENTS**
*Créer un paiement*
POST /api/payments/
Description : Initie un processus de paiement (article unique ou panier complet)
Body :
json

{
  "listing_id": 1,        // Optionnel - pour un seul article
  "payment_method": "mobile_money"
}

Comportement :

    Si listing_id fourni : paiement d'un seul article

    Si listing_id omis : paiement du panier complet

    Validation automatique du stock et du panier

Réponse (Paiement panier) :
json

{
  "status": "requires_payment_method",
  "transaction_ids": [1, 2, 3],
  "payment_intent_id": "pi_xxx",
  "client_secret": "pi_xxx_secret_xxx",
  "total_amount": 25000.50,
  "total_commission": 1750.04,
  "total_net_amount": 23250.46,
  "items_count": 3,
  "currency": "xof",
  "items": [
    {
      "listing_id": 1,
      "listing_title": "iPhone 13",
      "quantity": 1,
      "unit_price": 800.00,
      "total_price": 800.00,
      "commission": 56.00,
      "net_amount": 744.00
    }
  ]
}

*Récupérer le récapitulatif de paiement*
GET /api/payments/summary/
Description : Calcul détaillé du panier avant paiement (sans commission pour l'acheteur)
Réponse :
json

{
  "sous_total": 24000.50,
  "frais_livraison": 1000,
  "total_general": 25000.50,
  "items_count": 2,
  "items_details": [
    {
      "listing_id": 1,
      "listing_title": "iPhone 13",
      "quantity": 1,
      "unit_price": 800.00,
      "total_price": 800.00
    }
  ],
  "currency": "XOF",
  "note_commission": "La commission de 5% sera déduite lors du transfert au vendeur"
}

*Confirmer un paiement*
POST /api/payments/confirm/
Description : Vérifie le statut Stripe et finalise les transactions
Body :
json

{
  "payment_intent_id": "pi_xxx"
}

Réponse :
json

{
  "status": "succeeded",
  "message": "Paiement confirmé avec succès - 3 transactions",
  "transactions_completed": 3,
  "panier_vide": true
}

# 📊 GESTION DES TRANSACTIONS
*Lister mes transactions*
GET /api/payments/
Description : Récupère toutes les transactions où l'utilisateur est acheteur ou vendeur
Réponse : Liste des transactions avec détails complets

*Détails d'une transaction*
GET /api/payments/{id}/
Description : Informations détaillées d'une transaction spécifique
Inclus : Statut Stripe et montant reçu si disponible

*Rembourser une transaction*
POST /api/payments/{id}/refund/
Permissions : Vendeur seulement
Description : Initie un remboursement Stripe et réactive l'annonce
Réponse :
json

{
  "status": "refunded",
  "refund_id": "re_xxx",
  "message": "Transaction 1 remboursée avec succès"
}

# 🧹 NETTOYAGE & GESTION POST-PAIEMENT
*Vider le panier après paiement*
POST /api/payments/clear-cart/
Description : Nettoie le panier après confirmation de paiement réussi
Body :
json

{
  "payment_intent_id": "pi_xxx"
}

Réponse :
json

{
  "message": "Panier vidé avec succès (3 articles)",
  "items_removed": 3
}

*Nettoyer les transactions abandonnées*
POST /api/payments/cleanup/
Description : Supprime les transactions en statut "pending" abandonnées
Body :
json

{
  "payment_intent_id": "pi_xxx"
}

Réponse :
json

{
  "message": "2 transactions pending supprimées",
  "cleaned": true
}