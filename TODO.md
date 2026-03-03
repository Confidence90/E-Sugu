# TODO: Refactoring Logistique, Paiement et Multi-vendeurs

## Objectifs
- Séparer logistique et paiement
- Corriger les incohérences buyer/user
- Supporter panier multi-vendeurs
- Préparer litige + auto-release

## Tâches

### 1. Nettoyer Order model (commandes/models.py)
- [ ] 1.1 Supprimer le champ `user` redondant, garder seulement `buyer`
- [ ] 1.2 Ajouter champ `is_escrow` existant mais améliorer la logique
- [ ] 1.3 Ajouter champs pour le litige (dispute)
- [ ] 1.4 Corriger `release_payment_to_seller()` pour utiliser 'held'

### 2. Améliorer Transaction model (payments/models.py)
- [ ] 2.1 Ajouter statut 'held' pour escrow
- [ ] 2.2 Corriger `create_order_after_payment()` pour créer avec 'pending' pas 'completed'
- [ ] 2.3 Ajouter méthode pour libérer le paiement lors de la confirmation livraison

### 3. Mettre à jour le flux de paiement (payments/views.py)
- [ ] 3.1 Créer les transactions avec statut 'pending' (pas 'held' encore)
- [ ] 3.2 Lors de la confirmation Stripe: mettre à 'held' (escrow)

### 4. Mettre à jour les vues commandes
- [ ] 4.1 Corriger les vues pour utiliser `buyer` au lieu de `user`
- [ ] 4.2 Implémenter la confirmation de livraison qui libère le paiement

### 5. Ajouter gestion des litiges
- [ ] 5.1 Ajouter modèle Dispute ou champs dans Order
- [ ] 5.2 Implémenter auto-release après délai

## Notes
- Garder la rétrocompatibilité autant que possible
- Les migrations seront nécessaires après les changements de modèle
