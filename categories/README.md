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