# create_test_reviews.py
import os
import django
from django.utils import timezone
from django.db.models import Avg

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_sugu.settings')
django.setup()

from users.models import User
from reviews.models import Review

def create_test_reviews():
    print("🚀 Création des avis de test...")
    
    # Récupérer le vendeur
    seller = User.objects.get(email='vendeur@test.com')
    
    # Récupérer d'autres utilisateurs pour être les reviewers
    reviewers = User.objects.exclude(email='vendeur@test.com')[:3]
    
    # Créer des avis de test
    reviews_data = [
        {"rating": 5, "comment": "Excellent vendeur, livraison rapide !"},
        {"rating": 4, "comment": "Bon service, produit conforme"},
        {"rating": 3, "comment": "Correct, mais délai un peu long"}
    ]
    
    for i, reviewer in enumerate(reviewers):
        if i < len(reviews_data):
            review, created = Review.objects.get_or_create(
                reviewer=reviewer,
                reviewed=seller,
                defaults=reviews_data[i]
            )
            if created:
                print(f"✅ Avis créé: {reviewer.email} → {seller.email} ({review.rating}⭐)")
    
    # Afficher le récapitulatif
    seller_reviews = Review.objects.filter(reviewed=seller)
    print(f"\n📋 Avis pour {seller.email}:")
    print(f"Total: {seller_reviews.count()}")
    avg_rating = seller_reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    print(f"Note moyenne: {avg_rating:.1f}⭐")

if __name__ == '__main__':
    create_test_reviews()