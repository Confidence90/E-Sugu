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