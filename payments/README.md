#   📋 Documentation des URLs Paiements

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

### 📊 RÉSUMÉ COMPLET DES ENDPOINTS
**Méthode	URL	Description**
POST	/	Créer un paiement (article ou panier)
GET	/	Lister mes transactions
GET	/summary/	Récapitulatif avant paiement
POST	/confirm/	Confirmer un paiement
GET	/{id}/	Détails d'une transaction
POST	/{id}/refund/	Rembourser une transaction
POST	/clear-cart/	Vider panier après paiement
POST	/cleanup/	Nettoyer transactions abandonnées

#🛡️ RÈGLES DE GESTION DES PAIEMENTS
*Validation Automatique*

    ✅ Panier non vide : Vérification immédiate

    ✅ Stock disponible : Validation quantité vs stock

    ✅ Numéro de téléphone : Requis pour Mobile Money

    ✅ Montant minimum : Validation Stripe (≥ 100 XOF)

*Workflow de Paiement Panier*

    Validation → GET /summary/ (optionnel)

    Initiation → POST / (sans listing_id)

    Paiement → Client utilise client_secret avec Stripe

    Confirmation → POST /confirm/

    Nettoyage → POST /clear-cart/ (automatique ou manuel)

*Statuts des Transactions*

    pending : Paiement initié

    completed : Paiement réussi

    refunded : Remboursement effectué

    failed : Échec du paiement

#   💰 CALCULS FINANCIERS
*Pour le panier complet*
text

Sous-total = Σ(prix_unitaires × quantités)
Frais livraison = 1000 XOF (fixe)
Total général = Sous-total + Frais livraison

Commission (côté vendeur)
text

Commission = 7% du montant de chaque article
Montant net vendeur = Total article - Commission

# 🎯 EXEMPLES D'UTILISATION COMPLETS
**Workflow Panier Complet**
*Vérifier le récapitulatif*
bash

GET /api/payments/summary/

*Initier le paiement*
bash

POST /api/payments/
{
  "payment_method": "mobile_money"
}

*Traiter le paiement côté client*
javascript

// Utiliser stripe.confirmPayment() avec le client_secret

*Confirmer le paiement*
bash

POST /api/payments/confirm/
{
  "payment_intent_id": "pi_xxx"
}

*Vider le panier (automatique ou manuel)*
bash

POST /api/payments/clear-cart/
{
  "payment_intent_id": "pi_xxx"
}

*Workflow Article Unique*
bash

POST /api/payments/
{
  "listing_id": 1,
  "payment_method": "mobile_money"
}

Gestion des Remboursements
bash

POST /api/payments/1/refund/
# Seulement pour le vendeur

Nettoyage des Échecs
bash

POST /api/payments/cleanup/
{
  "payment_intent_id": "pi_xxx"
}

**⚠️ NOTES IMPORTANTES**

    Mobile Money uniquement : Support pour Orange Money, MTN Mobile Money, etc.

    Devise XOF : Tous les montants en Franc CFA

    Commission 7% : Déduite automatiquement pour le vendeur

    Panier obligatoire : Pour les paiements sans listing_id

    Sécurité : Chaque utilisateur ne voit que ses propres transactions

    Intégration Stripe : Utilise les Payment Intents pour une sécurité maximale

**🔄 INTÉGRATION AVEC PANIER**

Le système de paiement est étroitement lié au panier :

    ✅ Validation automatique du panier avant paiement

    ✅ Création multiple de transactions depuis le panier

    ✅ Vidage automatique après confirmation

    ✅ Gestion des stocks en temps réel