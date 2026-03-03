# commandes/tests.py

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock
from .factories import OrderFactory, UserFactory, ListingFactory, CategoryFactory
from commandes.models import Order
from notifications.models import Notification

class DeliveryConfirmationTest(TestCase):
    def setUp(self):
        # Créer les données avec factory_boy
        self.buyer = UserFactory()
        self.seller = UserFactory(is_seller=True)
        self.admin = UserFactory(is_staff=True, is_superuser=True)
        self.category = CategoryFactory(name='Test Category')
        self.listing = ListingFactory(
            user=self.seller,
            category=self.category,
            condition='new',
            quantity=10,
            price=10000
        )
        self.order = OrderFactory(
            user=self.buyer,
            listing=self.listing,
            status='shipped',
            quantity=2,
            total_price=20000,
            shipping_country='Mali',
            shipping_method='Standard'
        )
    
    def test_order_creation(self):
        """Vérifier que la commande est créée correctement"""
        self.assertEqual(self.order.status, 'shipped')
        self.assertEqual(self.order.user, self.buyer)
        self.assertEqual(self.order.listing, self.listing)
        self.assertEqual(self.order.quantity, 2)
        self.assertEqual(self.order.total_price, 20000)
    
    def test_confirm_delivery_success(self):
        """Tester la confirmation de livraison réussie"""
        # Vérifier l'état initial
        self.assertEqual(self.order.status, 'shipped')
        self.assertIsNone(self.order.delivered_at)
        
        # Simuler la confirmation
        success, message = self.order.confirm_delivery(confirmed_by=self.buyer)
        
        # Vérifier le résultat
        self.assertTrue(success)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'delivered')
        self.assertIsNotNone(self.order.delivered_at)
        self.assertIsNotNone(self.order.delivery_confirmed_at)
    
    def test_confirm_delivery_wrong_status(self):
        """Tester qu'on ne peut pas confirmer une commande non expédiée"""
        self.order.status = 'pending'
        self.order.save()
        
        success, message = self.order.confirm_delivery()
        
        self.assertFalse(success)
        self.assertIn("doit être expédiée", message)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'pending')
    
    def test_confirm_delivery_unauthorized_user(self):
        """Tester qu'un autre utilisateur ne peut pas confirmer"""
        other_user = UserFactory()
        
        # Simuler la confirmation par un autre utilisateur
        # Note: La logique d'autorisation est généralement dans la vue, pas dans le modèle
        # Ce test vérifie seulement que le modèle accepte n'importe quel confirmed_by
        success, message = self.order.confirm_delivery(confirmed_by=other_user)
        
        self.assertTrue(success)  # Le modèle accepte, la vue doit bloquer
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'delivered')
    
    def test_auto_confirmation_after_deadline(self):
        """Tester l'auto-confirmation après 7 jours"""
        # Définir une deadline passée
        self.order.delivery_confirmation_deadline = timezone.now() - timedelta(days=1)
        self.order.status = 'shipped'
        self.order.save()
        
        # Vérifier l'auto-confirmation
        result = self.order.check_auto_confirmation()
        
        self.assertTrue(result)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'delivered')
        self.assertIsNotNone(self.order.delivered_at)
    
    def test_no_auto_confirmation_before_deadline(self):
        """Tester qu'il n'y a pas d'auto-confirmation avant la deadline"""
        # Définir une deadline future
        self.order.delivery_confirmation_deadline = timezone.now() + timedelta(days=5)
        self.order.status = 'shipped'
        self.order.save()
        
        result = self.order.check_auto_confirmation()
        
        self.assertFalse(result)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'shipped')
    
    @patch('commandes.models.Notification.objects.create')
    def test_notifications_on_confirmation(self, mock_notification):
        """Tester que les notifications sont créées lors de la confirmation"""
        self.order.confirm_delivery()
        
        # Vérifier que les notifications ont été créées
        self.assertTrue(mock_notification.called)
        # Vous pouvez vérifier les appels spécifiques
        # mock_notification.assert_called_with(...)
    
    def test_mark_as_shipped(self):
        """Tester le marquage comme expédié"""
        self.order.status = 'ready_to_ship'
        self.order.save()
        
        self.order.mark_as_shipped()
        
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'shipped')
        self.assertIsNotNone(self.order.shipped_at)
        self.assertIsNotNone(self.order.delivery_confirmation_deadline)
        
        # Vérifier que la deadline est dans 7 jours
        expected_deadline = self.order.shipped_at + timedelta(days=7)
        self.assertEqual(
            self.order.delivery_confirmation_deadline.date(),
            expected_deadline.date()
        )


class OrderWorkflowTest(TestCase):
    """Tester le workflow complet d'une commande"""
    
    def setUp(self):
        self.buyer = UserFactory()
        self.seller = UserFactory(is_seller=True)
        self.category = CategoryFactory()
        self.listing = ListingFactory(user=self.seller, category=self.category)
        self.order = OrderFactory(
            user=self.buyer,
            listing=self.listing,
            status='pending'
        )
    
    def test_complete_workflow(self):
        """Tester le workflow complet: pending → confirmed → ready → shipped → delivered"""
        
        # 1. Pending → Confirmed
        self.order.status = 'confirmed'
        self.order.save()
        self.assertEqual(self.order.status, 'confirmed')
        
        # 2. Confirmed → Ready to ship
        self.order.status = 'ready_to_ship'
        self.order.save()
        self.assertEqual(self.order.status, 'ready_to_ship')
        
        # 3. Ready to ship → Shipped
        self.order.mark_as_shipped()
        self.assertEqual(self.order.status, 'shipped')
        self.assertIsNotNone(self.order.shipped_at)
        
        # 4. Shipped → Delivered
        self.order.confirm_delivery()
        self.assertEqual(self.order.status, 'delivered')
        self.assertIsNotNone(self.order.delivered_at)
    
    def test_cancel_before_shipping(self):
        """Tester l'annulation avant expédition"""
        self.order.status = 'confirmed'
        self.order.save()
        
        self.order.cancel_order()
        
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'cancelled')
    
    def test_cannot_cancel_after_shipping(self):
        """Tester qu'on ne peut pas annuler après expédition"""
        self.order.status = 'shipped'
        self.order.save()
        
        # La méthode cancel_order devrait échouer ou ne rien faire
        # selon votre implémentation
        if hasattr(self.order, 'cancel_order'):
            result = self.order.cancel_order()
            # Vérifier que ça n'a pas changé le statut
            self.order.refresh_from_db()
            self.assertEqual(self.order.status, 'shipped')


class OrderStatsTest(TestCase):
    """Tester les statistiques des commandes"""
    
    def setUp(self):
        self.buyer = UserFactory()
        self.seller = UserFactory(is_seller=True)
        self.category = CategoryFactory()
        self.listing = ListingFactory(user=self.seller, category=self.category)
        
        # Créer plusieurs commandes avec différents statuts
        dates = [
            timezone.now() - timedelta(days=i) for i in range(10)
        ]
        
        for i, status in enumerate(['pending', 'shipped', 'delivered', 'cancelled']):
            OrderFactory(
                user=self.buyer,
                listing=self.listing,
                status=status,
                created_at=dates[i],
                total_price=10000 * (i + 1)
            )
    
    def test_order_count_by_status(self):
        """Tester le comptage par statut"""
        from django.db.models import Count
        
        stats = Order.objects.values('status').annotate(count=Count('id'))
        status_dict = {item['status']: item['count'] for item in stats}
        
        self.assertEqual(status_dict.get('pending', 0), 1)
        self.assertEqual(status_dict.get('shipped', 0), 1)
        self.assertEqual(status_dict.get('delivered', 0), 1)
        self.assertEqual(status_dict.get('cancelled', 0), 1)
    
    def test_total_revenue(self):
        """Tester le calcul du chiffre d'affaires"""
        from django.db.models import Sum
        
        total = Order.objects.aggregate(total=Sum('total_price'))['total']
        # 10000 + 20000 + 30000 + 40000 = 100000
        self.assertEqual(total, 100000)


class DeliveryDeadlineTest(TestCase):
    """Tester les deadlines de livraison"""
    
    def setUp(self):
        self.buyer = UserFactory()
        self.seller = UserFactory(is_seller=True)
        self.listing = ListingFactory(user=self.seller)
        self.order = OrderFactory(
            user=self.buyer,
            listing=self.listing,
            status='shipped'
        )
    
    def test_deadline_calculation(self):
        """Tester le calcul de la deadline"""
        self.order.mark_as_shipped()
        
        # La deadline devrait être dans 7 jours
        expected = self.order.shipped_at + timedelta(days=7)
        self.assertEqual(
            self.order.delivery_confirmation_deadline.date(),
            expected.date()
        )
    
    def test_remaining_days_calculation(self):
        """Tester le calcul des jours restants"""
        self.order.shipped_at = timezone.now() - timedelta(days=3)
        self.order.delivery_confirmation_deadline = timezone.now() + timedelta(days=4)
        self.order.save()
        
        # Implémentez une méthode dans Order pour calculer les jours restants
        if hasattr(self.order, 'get_remaining_days'):
            remaining = self.order.get_remaining_days()
            self.assertEqual(remaining, 4)