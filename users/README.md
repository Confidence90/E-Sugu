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