# create_test_data.py - À la racine du projet
import os
import django
from django.utils import timezone
from datetime import timedelta

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_sugu.settings')
django.setup()

from users.models import User
from listings.models import Listing, ListingView, Category
from categories.models import Category as CatModel
from django.db import transaction

@transaction.atomic
def create_test_data():
    print("🚀 Création des données de test...")
    
    # Créer un vendeur de test
    seller, created = User.objects.get_or_create(
        email='vendeur@test.com',
        defaults={
            'first_name': 'Test',
            'last_name': 'Vendeur',
            'username': 'vendeur_test',
            'phone': '12345678',
            'country_code': '+223',
            'phone_full': '+22312345678',
            'is_seller': True,
            'is_active': True,
            'role': 'seller',
            'password': 'pbkdf2_sha256$870000$abc123$def456=='  # Mot de passe factice
        }
    )
    
    if created:
        seller.set_password('test123')
        seller.save()
        print("✅ Vendeur de test créé")
    else:
        print("✅ Vendeur de test existe déjà")
    
    # Créer une catégorie de test
    category, cat_created = CatModel.objects.get_or_create(
        name='Électronique',
        defaults={'description': 'Produits électroniques'}
    )
    
    # Créer des annonces de test
    listing, listing_created = Listing.objects.get_or_create(
        title='Smartphone Test',
        defaults={
            'description': 'Un smartphone de test pour les statistiques',
            'price': 150000,
            'quantity': 10,
            'quantity_sold': 2,
            'type': 'sale',
            'condition': 'new',
            'status': 'active',
            'location': 'Bamako',
            'category': category,
            'user': seller,
            'views_count': 0,
            'unique_visitors': 0
        }
    )
    
    if listing_created:
        print("✅ Annonce de test créée")
    else:
        print("✅ Annonce de test existe déjà")
    
    # Créer des vues de test
    views_created = 0
    for i in range(15):
        view, created = ListingView.objects.get_or_create(
            listing=listing,
            ip_address=f'192.168.1.{i % 10}',  # 10 IPs uniques
            user_agent=f'Test Browser {i}',
            session_key=f'test_session_{i}',
            defaults={'viewed_at': timezone.now() - timedelta(days=i % 7)}
        )
        if created:
            views_created += 1
    
    print(f"✅ {views_created} vues créées pour l'annonce {listing.id}")
    
    # Mettre à jour les compteurs de l'annonce
    listing.views_count = ListingView.objects.filter(listing=listing).count()
    listing.unique_visitors = ListingView.objects.filter(listing=listing).values('ip_address').distinct().count()
    listing.save()
    
    print(f"📊 Annonce {listing.id}: {listing.views_count} vues, {listing.unique_visitors} visiteurs uniques")
    
    # Afficher les données créées
    print("\n📋 Récapitulatif des données créées:")
    print(f"Vendeur: {seller.email} (ID: {seller.id})")
    print(f"Annonce: '{listing.title}' (ID: {listing.id})")
    print(f"Vues totales: {listing.views_count}")
    print(f"Visiteurs uniques: {listing.unique_visitors}")
    print(f"Vues détaillées en base: {ListingView.objects.filter(listing=listing).count()}")

if __name__ == '__main__':
    create_test_data()