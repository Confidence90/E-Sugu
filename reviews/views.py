# reviews/views.py - AJOUTEZ ces vues
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status, generics
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Count, Q, F, Min, Max, Sum
from django.utils import timezone

        
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from .models import Review
from .serializers import (
    ReviewSerializer, 
    CreateReviewSerializer,
    PlatformReviewCreateSerializer,
    ReplySerializer,
    VoteSerializer,
    SellerReviewSerializer
)
from users.models import User

class ReviewView(generics.ListCreateAPIView):
    """Vue pour créer et lister des avis"""
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Retourne les avis reçus par l'utilisateur connecté
        return Review.objects.filter(reviewed=self.request.user).order_by('-created_at')
    
    def post(self, request, *args, **kwargs):
        serializer = CreateReviewSerializer(data=request.data, context={'reviewer': request.user})
        if serializer.is_valid():
            review = serializer.save(reviewer=request.user)
            
            # Si c'est un achat vérifié, marquer comme tel
            if request.data.get('order_id'):
                # Vérifier si l'utilisateur a effectué un achat
                from commandes.models import Order
                order = Order.objects.filter(
                    buyer=request.user,
                    listing__user=review.reviewed,
                    status='completed'
                ).first()
                if order:
                    review.is_verified_purchase = True
                    review.save()
            
            # Mettre à jour les statistiques
            review.update_rating_stats()
            
            return Response(
                ReviewSerializer(review, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vue pour récupérer, mettre à jour ou supprimer un avis"""
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return get_object_or_404(Review, id=self.kwargs['id'])
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Vérifier que l'utilisateur est bien l'auteur de l'avis
        if instance.reviewer != request.user:
            return Response(
                {'error': "Vous ne pouvez pas modifier cet avis."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Ne permettre que la modification du commentaire
        data = request.data.copy()
        if 'rating' in data:
            data.pop('rating')  # Ne pas permettre la modification de la note
        
        serializer = self.get_serializer(instance, data=data, partial=True)
        if serializer.is_valid():
            serializer.save(is_edited=True, edit_date=timezone.now())
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Vérifier que l'utilisateur est bien l'auteur de l'avis
        if instance.reviewer != request.user and not request.user.is_staff:
            return Response(
                {'error': "Vous ne pouvez pas supprimer cet avis."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        self.perform_destroy(instance)
        
        # Mettre à jour les statistiques
        instance.update_rating_stats()
        
        return Response(status=status.HTTP_204_NO_CONTENT)

class UserReviewsView(APIView):
    """Avis sur un utilisateur spécifique"""
    permission_classes = [AllowAny]
    
    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'Utilisateur non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        reviews = Review.objects.filter(reviewed=user).order_by('-created_at')
        
        # Statistiques
        stats = reviews.aggregate(
            average_rating=Avg('rating'),
            total_reviews=Count('id'),
            verified_purchases=Count('id', filter=Q(is_verified_purchase=True))
        )
        
        # Distribution des notes
        rating_distribution = {}
        for rating in range(1, 6):
            rating_distribution[rating] = reviews.filter(rating=rating).count()
        
        serializer = ReviewSerializer(reviews, many=True, context={'request': request})
        
        return Response({
            'user': {
                'id': user.id,
                'name': user.get_full_name(),
                'average_rating': stats['average_rating'] or 0,
                'total_reviews': stats['total_reviews'] or 0,
            },
            'stats': {
                **stats,
                'rating_distribution': rating_distribution,
                'verified_percentage': (
                    (stats['verified_purchases'] / stats['total_reviews'] * 100) 
                    if stats['total_reviews'] > 0 else 0
                )
            },
            'reviews': serializer.data,
            'can_review': self._can_user_review(request.user, user)
        })
    
    def _can_user_review(self, current_user, target_user):
        """Vérifier si l'utilisateur connecté peut évaluer cet utilisateur"""
        if not current_user.is_authenticated:
            return False
        
        if current_user == target_user:
            return False
        
        # Vérifier s'il y a eu une transaction entre les deux utilisateurs
        from commandes.models import Order
        has_transaction = Order.objects.filter(
            Q(buyer=current_user, listing__user=target_user) |
            Q(buyer=target_user, listing__user=current_user),
            status='completed'
        ).exists()
        
        return has_transaction

# reviews/views.py - MODIFIEZ PlatformReviewsView
class PlatformReviewsView(APIView):
    """Avis sur la plateforme elle-même"""
    permission_classes = [AllowAny]
    
    def get_platform_user(self):
        """Récupérer un admin/superutilisateur existant pour représenter la plateforme"""
        # Chercher d'abord un superutilisateur avec un email spécifique
        platform_user = User.objects.filter(
            email='admin@e-sugu.com',
            is_superuser=True
        ).first()
        
        # Sinon, prendre le premier superutilisateur
        if not platform_user:
            platform_user = User.objects.filter(
                is_superuser=True
            ).first()
        
        # Sinon, prendre le premier admin (staff)
        if not platform_user:
            platform_user = User.objects.filter(
                is_staff=True
            ).first()
        
        # Si toujours pas, prendre l'utilisateur avec ID 1 (souvent le superadmin)
        request_user = self.request.user if hasattr(self, 'request') else None
        if request_user and request_user.is_authenticated and platform_user and request_user.id == platform_user.id:
            # Si l'utilisateur connecté EST l'admin, prendre un autre admin ou créer un spécial
            other_admin = User.objects.filter(
                is_superuser=True
            ).exclude(id=request_user.id).first()
            
            if other_admin:
                platform_user = other_admin
            else:
                # Créer un utilisateur spécial pour la plateforme
                try:
                    platform_user = User.objects.create(
                        email='platform@e-sugu.com',
                        username='e-sugu-platform',
                        first_name='E-Sugu',
                        last_name='Administration',
                        is_active=True,
                        is_verified=True,
                        is_staff=True,
                        is_superuser=False,
                        role='admin'
                    )
                    platform_user.set_unusable_password()
                    platform_user.save()
                    print(f"✅ Utilisateur plateforme spécial créé: {platform_user.email}")
                except:
                    # Si création échoue, utiliser quand même l'admin connecté
                    print(f"⚠️ Utilisation de l'admin connecté pour la plateforme")
        
        return platform_user
    
    def get(self, request):
        """Récupérer tous les avis sur la plateforme"""
        platform_user = self.get_platform_user()
        
        if not platform_user:
            return Response({
                'platform_stats': {
                    'average_rating': 0,
                    'total_reviews': 0,
                },
                'reviews': []
            })
        
        # Récupérer les avis sur la plateforme
        platform_reviews = Review.objects.filter(
            reviewed=platform_user,
            review_type='platform'
        ).order_by('-created_at')
        
        # Statistiques de la plateforme
        stats = platform_reviews.aggregate(
            average_rating=Avg('rating'),
            total_reviews=Count('id')
        )
        
        # Distribution des notes
        rating_distribution = {}
        for rating in range(1, 6):
            rating_distribution[rating] = platform_reviews.filter(rating=rating).count()
        
        serializer = ReviewSerializer(platform_reviews, many=True, context={'request': request})
        
        return Response({
            'platform': {
                'id': platform_user.id,
                'name': platform_user.get_full_name() or 'Administration E-Sugu',
                'email': platform_user.email,
                'role': platform_user.role,
                'is_admin': True,
                'average_rating': stats['average_rating'] or 0,
                'total_reviews': stats['total_reviews'] or 0,
                'rating_distribution': rating_distribution
            },
            'reviews': serializer.data
        })
    
    def post(self, request):
        """Donner son avis sur la plateforme - VERSION SIMPLIFIÉE"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Vous devez être connecté pour donner votre avis'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Récupérer l'admin plateforme (celui avec ID 4 d'après vos logs)
        platform_user = User.objects.filter(
            is_superuser=True
        ).exclude(id=request.user.id).first()  # Exclure l'utilisateur connecté
        
        # Si aucun autre superuser n'existe, créer un utilisateur spécial
        if not platform_user:
            try:
                platform_user = User.objects.create(
                    email='platform-admin@e-sugu.com',
                    username='e-sugu-platform',
                    first_name='E-Sugu',
                    last_name='Plateforme',
                    is_active=True,
                    is_verified=True,
                    is_staff=True,
                    is_superuser=False,
                    role='admin'
                )
                platform_user.set_unusable_password()
                platform_user.save()
                print(f"✅ Création d'un admin spécial pour la plateforme")
            except Exception as e:
                print(f"❌ Erreur création admin: {e}")
                # Utiliser l'utilisateur connecté en dernier recours
                platform_user = request.user
        
        # Vérifier si l'utilisateur a déjà donné son avis sur la plateforme
        if Review.objects.filter(
            reviewer=request.user, 
            reviewed=platform_user,
            review_type='platform'
        ).exists():
            return Response(
                {'error': 'Vous avez déjà donné votre avis sur la plateforme'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validation manuelle
        rating = request.data.get('rating')
        comment = request.data.get('comment')
        
        if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
            return Response(
                {'error': 'La note doit être un entier entre 1 et 5'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not comment or len(comment.strip()) < 5:
            return Response(
                {'error': 'Le commentaire doit contenir au moins 5 caractères'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Créer l'avis DIRECTEMENT sans serializer pour éviter la validation
        try:
            review = Review.objects.create(
                reviewer=request.user,
                reviewed=platform_user,
                rating=rating,
                comment=comment.strip(),
                review_type='platform'
            )
            
            # Mettre à jour les statistiques
            review.update_rating_stats()
            
            print(f"✅ Avis plateforme créé avec succès!")
            print(f"   - ID: {review.id}")
            print(f"   - Reviewer: {review.reviewer.email}")
            print(f"   - Reviewed: {review.reviewed.email}")
            print(f"   - Rating: {review.rating}")
            
            return Response(
                ReviewSerializer(review, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            print(f"❌ Erreur création avis: {str(e)}")
            return Response(
                {'error': f'Erreur lors de la création de l\'avis: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

class ReplyToReviewView(APIView):
    """Répondre à un avis (pour les vendeurs)"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, review_id):
        try:
            review = Review.objects.get(id=review_id)
        except Review.DoesNotExist:
            return Response(
                {'error': 'Avis non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Vérifier que l'utilisateur est celui qui a été évalué
        if review.reviewed != request.user:
            return Response(
                {'error': 'Vous ne pouvez répondre qu\'aux avis vous concernant'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ReplySerializer(data=request.data)
        if serializer.is_valid():
            review.seller_reply = serializer.validated_data['reply']
            review.reply_date = timezone.now()
            review.save()
            
            return Response(
                ReviewSerializer(review, context={'request': request}).data
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VoteOnReviewView(APIView):
    """Voter sur l'utilité d'un avis"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, review_id):
        try:
            review = Review.objects.get(id=review_id)
        except Review.DoesNotExist:
            return Response(
                {'error': 'Avis non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Empêcher l'auteur de voter sur son propre avis
        if review.reviewer == request.user:
            return Response(
                {'error': 'Vous ne pouvez pas voter sur votre propre avis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = VoteSerializer(data=request.data)
        if serializer.is_valid():
            is_helpful = serializer.validated_data['is_helpful']
            
            # Utiliser un système de cache pour empêcher les votes multiples
            cache_key = f"review_vote_{review_id}_{request.user.id}"
            from django.core.cache import cache
            
            if cache.get(cache_key):
                return Response(
                    {'error': 'Vous avez déjà voté sur cet avis'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Mettre à jour les compteurs
            if is_helpful:
                review.helpful_count += 1
            else:
                review.not_helpful_count += 1
            review.save()
            
            # Mettre en cache le vote (24h)
            cache.set(cache_key, True, 60*60*24)
            
            return Response({
                'message': 'Vote enregistré',
                'helpful_count': review.helpful_count,
                'not_helpful_count': review.not_helpful_count,
                'helpful_percentage': review.helpful_score
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# Ajoutez une vue de test pour déboguer
@api_view(['GET'])
@permission_classes([AllowAny])
def debug_platform_info(request):
    """Endpoint pour déboguer les informations de la plateforme"""
    # Vérifier tous les superusers
    superusers = User.objects.filter(is_superuser=True).values('id', 'email', 'first_name', 'last_name')
    
    # Vérifier l'utilisateur connecté
    current_user = None
    if request.user.is_authenticated:
        current_user = {
            'id': request.user.id,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'is_superuser': request.user.is_superuser,
            'is_staff': request.user.is_staff,
        }
    
    # Logique pour déterminer l'admin plateforme
    platform_admin = None
    logic = []
    
    # 1. Chercher admin@e-sugu.com
    admin1 = User.objects.filter(email='admin@e-sugu.com', is_superuser=True).first()
    logic.append(f"1. admin@e-sugu.com: {admin1.email if admin1 else 'Non trouvé'}")
    if admin1:
        platform_admin = admin1
    
    # 2. Premier superuser
    if not platform_admin:
        admin2 = User.objects.filter(is_superuser=True).first()
        logic.append(f"2. Premier superuser: {admin2.email if admin2 else 'Non trouvé'}")
        if admin2:
            platform_admin = admin2
    
    # 3. Créer un spécial
    if not platform_admin:
        logic.append("3. Aucun superuser trouvé, création nécessaire")
    
    return Response({
        'current_user': current_user,
        'platform_admin': {
            'id': platform_admin.id if platform_admin else None,
            'email': platform_admin.email if platform_admin else None,
            'name': platform_admin.get_full_name() if platform_admin else None,
        },
        'available_superusers': list(superusers),
        'logic_steps': logic,
        'review_count': Review.objects.filter(review_type='platform').count()
    })

class ListingReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, listing_id):
        from listings.models import Listing
        from commandes.models import Order

        listing = get_object_or_404(Listing, id=listing_id)

        # Interdire l’auto-évaluation
        if listing.user == request.user:
            return Response(
                {'error': "Vous ne pouvez pas évaluer votre propre annonce."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Vérifier achat confirmé
        has_bought = Order.objects.filter(
            buyer=request.user,
            listing=listing,
            status__in=Order.COMPLETED_STATUSES
        ).exists()

        if not has_bought:
            return Response(
                {'error': "Vous devez avoir acheté ce produit pour l’évaluer."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Empêcher doublon
        if Review.objects.filter(
            reviewer=request.user,
            reviewed=listing.user,  # ← Ajouter cette ligne pour vérifier l'annonce spécifique
            review_type='product'
        ).exists():
            return Response(
                {'error': "Vous avez déjà évalué cette annonce."},
                status=status.HTTP_400_BAD_REQUEST
            )

        rating = request.data.get('rating')
        comment = request.data.get('comment')

        if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
            return Response({'error': 'Note invalide'}, status=status.HTTP_400_BAD_REQUEST)

        if not comment or len(comment.strip()) < 5:
            return Response({'error': 'Commentaire trop court'}, status=status.HTTP_400_BAD_REQUEST)

        review = Review.objects.create(
            reviewer=request.user,
            reviewed=listing.user,
            rating=rating,
            comment=comment.strip(),
            review_type='product',
            is_verified_purchase=True
        )

        review.update_rating_stats()

        return Response(
            ReviewSerializer(review, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

class SellerReviewsView(APIView):
    """
    Endpoint pour que les vendeurs voient les avis sur leurs annonces
    SANS voir les coordonnées des acheteurs
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Vérifier que l'utilisateur est un vendeur
        if not request.user.is_seller:
            return Response(
                {'error': 'Accès réservé aux vendeurs'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Récupérer tous les avis où le vendeur est celui qui a été évalué
        reviews = Review.objects.filter(
            reviewed=request.user,
            review_type='product'  # Uniquement les avis sur les produits
        ).order_by('-created_at')
        
        # Statistiques pour le dashboard du vendeur
        stats = reviews.aggregate(
            average_rating=Avg('rating'),
            total_reviews=Count('id'),
            verified_purchases=Count('id', filter=Q(is_verified_purchase=True)),
            five_star_reviews=Count('id', filter=Q(rating=5)),
            one_star_reviews=Count('id', filter=Q(rating=1))
        )
        
        # Distribution des notes
        rating_distribution = {}
        for rating in range(1, 6):
            rating_distribution[rating] = reviews.filter(rating=rating).count()
        
        # Réponses aux avis
        replied_reviews = reviews.filter(seller_reply__isnull=False).count()
        
        # Pagination simple
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        start = (page - 1) * page_size
        end = start + page_size
        
        paginated_reviews = reviews[start:end]
        
        serializer = SellerReviewSerializer(
            paginated_reviews, 
            many=True, 
            context={'request': request}
        )
        
        return Response({
            'seller': {
                'id': request.user.id,
                'shop_name': getattr(request.user.vendor_profile, 'shop_name', ''),
                'total_reviews': stats['total_reviews'] or 0,
                'average_rating': round(stats['average_rating'] or 0, 1),
            },
            'stats': {
                'total_reviews': stats['total_reviews'] or 0,
                'average_rating': round(stats['average_rating'] or 0, 1),
                'verified_purchases': stats['verified_purchases'] or 0,
                'five_star_count': stats['five_star_reviews'] or 0,
                'one_star_count': stats['one_star_reviews'] or 0,
                'replied_reviews': replied_reviews,
                'rating_distribution': rating_distribution,
                'response_rate': (
                    (replied_reviews / stats['total_reviews'] * 100) 
                    if stats['total_reviews'] > 0 else 0
                ),
                'verified_percentage': (
                    (stats['verified_purchases'] / stats['total_reviews'] * 100) 
                    if stats['total_reviews'] > 0 else 0
                )
            },
            'reviews': serializer.data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_reviews': reviews.count(),
                'total_pages': (reviews.count() + page_size - 1) // page_size,
                'has_next': end < reviews.count(),
                'has_previous': page > 1
            }
        })


class SellerListingReviewsView(APIView):
    """
    Avis spécifiques à une annonce pour le vendeur
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, listing_id):
        from listings.models import Listing
        
        # Vérifier que l'utilisateur est un vendeur
        if not request.user.is_seller:
            return Response(
                {'error': 'Accès réservé aux vendeurs'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Vérifier que l'annonce appartient au vendeur
        try:
            listing = Listing.objects.get(id=listing_id, user=request.user)
        except Listing.DoesNotExist:
            return Response(
                {'error': 'Annonce non trouvée ou non autorisée'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Récupérer les avis pour cette annonce spécifique
        # Note: Vous devrez peut-être ajuster cette logique en fonction de votre modèle
        reviews = Review.objects.filter(
            reviewed=request.user,
            review_type='product'
        ).order_by('-created_at')
        
        # Filtrer par annonce si vous avez un champ de référence
        # Par exemple, si vous avez un champ ForeignKey vers Listing dans Review:
        # reviews = reviews.filter(listing=listing)
        
        # Pour l'instant, nous retournons tous les avis du vendeur
        # Vous pouvez ajouter une logique de filtrage spécifique plus tard
        
        serializer = SellerReviewSerializer(reviews, many=True, context={'request': request})
        
        # Statistiques pour cette annonce
        stats = reviews.aggregate(
            average_rating=Avg('rating'),
            total_reviews=Count('id')
        )
        
        return Response({
            'listing': {
                'id': listing.id,
                'title': listing.title,
                'average_rating': round(stats['average_rating'] or 0, 1),
                'total_reviews': stats['total_reviews'] or 0,
            },
            'reviews': serializer.data
        })
    
# reviews/views.py - AJOUTEZ cette vue
class SellerAverageRatingView(APIView):
    """
    Endpoint pour afficher la note moyenne du vendeur
    GET /api/reviews/seller/average-rating/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Vérifier que l'utilisateur est un vendeur
        if not request.user.is_seller:
            return Response(
                {'error': 'Accès réservé aux vendeurs'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Récupérer toutes les statistiques
        reviews = Review.objects.filter(
            reviewed=request.user,
            review_type='product'
        )
        
        stats = reviews.aggregate(
            average_rating=Avg('rating'),
            total_reviews=Count('id'),
            verified_purchases=Count('id', filter=Q(is_verified_purchase=True)),
            five_star_reviews=Count('id', filter=Q(rating=5)),
            four_star_reviews=Count('id', filter=Q(rating=4))
        )
        
        # Calculer le pourcentage d'avis positifs (4 et 5 étoiles)
        total = stats['total_reviews'] or 0
        positive_reviews = (stats['five_star_reviews'] or 0) + (stats['four_star_reviews'] or 0)
        positive_percentage = (positive_reviews / total * 100) if total > 0 else 0
        
        # Distribution par étoile
        distribution = {}
        for rating in range(1, 6):
            distribution[rating] = reviews.filter(rating=rating).count()
        
        # Avis récents (30 derniers jours)
        from django.utils import timezone
        from datetime import timedelta
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_reviews = reviews.filter(created_at__gte=thirty_days_ago).count()
        
        return Response({
            'seller': {
                'id': request.user.id,
                'shop_name': getattr(request.user.vendor_profile, 'shop_name', request.user.get_full_name),
                'avatar': request.user.avatar.url if request.user.avatar else None
            },
            'average_rating': {
                'value': round(stats['average_rating'] or 0, 1),
                'stars': '★★★★★'[:int(round(stats['average_rating'] or 0))] + '☆☆☆☆☆'[int(round(stats['average_rating'] or 0)):],
                'formatted': f"{round(stats['average_rating'] or 0, 1)}/5"
            },
            'summary': {
                'total_reviews': total,
                'verified_purchases': stats['verified_purchases'] or 0,
                'positive_reviews': positive_reviews,
                'positive_percentage': round(positive_percentage, 1),
                'recent_reviews': recent_reviews
            },
            'distribution': distribution,
            'comparison': {
                'platform_average': 4.2,  # Vous pouvez calculer cette valeur dynamiquement
                'difference': round((stats['average_rating'] or 0) - 4.2, 1) if total > 0 else 0,
                'trend': 'up' if recent_reviews > 0 and positive_percentage > 80 else 'stable'
            }
        })
    
# reviews/views.py - AJOUTEZ cette vue
class SellerPositiveReviewsView(APIView):
    """
    Endpoint pour afficher les avis positifs du vendeur (4 et 5 étoiles)
    GET /api/reviews/seller/positive-reviews/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Vérifier que l'utilisateur est un vendeur
        if not request.user.is_seller:
            return Response(
                {'error': 'Accès réservé aux vendeurs'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Récupérer uniquement les avis positifs (4 et 5 étoiles)
        positive_reviews = Review.objects.filter(
            reviewed=request.user,
            review_type='product',
            rating__in=[4, 5]
        ).order_by('-rating', '-created_at')
        
        # Statistiques des avis positifs
        stats = positive_reviews.aggregate(
            average_rating=Avg('rating'),
            total_positive=Count('id'),
            five_star_count=Count('id', filter=Q(rating=5)),
            four_star_count=Count('id', filter=Q(rating=4))
        )
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        start = (page - 1) * page_size
        end = start + page_size
        
        paginated_reviews = positive_reviews[start:end]
        
        serializer = SellerReviewSerializer(
            paginated_reviews, 
            many=True, 
            context={'request': request}
        )
        
        # Trier les avis par le plus récent et par note
        sorted_reviews = sorted(
            serializer.data,
            key=lambda x: (x['rating'], x['created_at']),
            reverse=True
        )
        rating_filter = request.query_params.get('rating')
        if rating_filter:
            if rating_filter == '5':
                positive_reviews = positive_reviews.filter(rating=5)
            elif rating_filter == '4':
                positive_reviews = positive_reviews.filter(rating=4)
        
        date_filter = request.query_params.get('period')
        if date_filter == 'week':
            from django.utils import timezone
            from datetime import timedelta
            week_ago = timezone.now() - timedelta(days=7)
            positive_reviews = positive_reviews.filter(created_at__gte=week_ago)

        return Response({
            'seller': {
                'id': request.user.id,
                'shop_name': getattr(request.user.vendor_profile, 'shop_name', request.user.get_full_name)
            },
            'stats': {
                'total_positive_reviews': stats['total_positive'] or 0,
                'five_star_count': stats['five_star_count'] or 0,
                'four_star_count': stats['four_star_count'] or 0,
                'average_positive_rating': round(stats['average_rating'] or 0, 1),
                'percentage_of_total': self._get_percentage_of_total(request.user, stats['total_positive'] or 0)
            },
            'highlights': self._get_positive_highlights(positive_reviews),
            'reviews': sorted_reviews,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_reviews': positive_reviews.count(),
                'total_pages': (positive_reviews.count() + page_size - 1) // page_size,
                'has_next': end < positive_reviews.count(),
                'has_previous': page > 1
            }
        })
    
    def _get_percentage_of_total(self, seller, positive_count):
        """Calculer le pourcentage d'avis positifs par rapport au total"""
        total_reviews = Review.objects.filter(
            reviewed=seller,
            review_type='product'
        ).count()
        
        if total_reviews > 0:
            return round((positive_count / total_reviews) * 100, 1)
        return 0
    
    def _get_positive_highlights(self, positive_reviews):
        """Extraire les points forts des avis positifs"""
        if not positive_reviews.exists():
            return []
        
        # Mots-clés positifs communs
        positive_keywords = ['excellent', 'super', 'génial', 'parfait', 'rapide', 
                           'conforme', 'qualité', 'recommandé', 'satisfait', 'professionnel']
        
        highlights = []
        
        # Analyse des commentaires
        from collections import Counter
        all_comments = " ".join([r.comment.lower() for r in positive_reviews])
        
        # Compter les mots-clés
        word_counts = Counter(all_comments.split())
        common_words = [(word, count) for word, count in word_counts.items() 
                       if word in positive_keywords][:5]
        
        # Avis avec les commentaires les plus longs (généralement plus détaillés)
        detailed_reviews = positive_reviews.order_by('-created_at')[:3]
        
        for review in detailed_reviews:
            highlights.append({
                'id': review.id,
                'rating': review.rating,
                'excerpt': review.comment[:100] + '...' if len(review.comment) > 100 else review.comment,
                'date': review.created_at.strftime('%d/%m/%Y')
            })
        
        return {
            'common_words': [{'word': word, 'count': count} for word, count in common_words],
            'detailed_reviews': highlights[:3]
        }
    
# reviews/views.py - AJOUTEZ cette vue
class SellerPendingReplyView(APIView):
    """
    Endpoint pour afficher les avis en attente de réponse
    GET /api/reviews/seller/pending-reply/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Vérifier que l'utilisateur est un vendeur
        if not request.user.is_seller:
            return Response(
                {'error': 'Accès réservé aux vendeurs'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Récupérer les avis sans réponse
        pending_reviews = Review.objects.filter(
            reviewed=request.user,
            review_type='product',
            seller_reply__isnull=True
        ).order_by('-created_at')
        
        # Statistiques
        stats = pending_reviews.aggregate(
            total_pending=Count('id'),
            average_rating=Avg('rating'),
            oldest_pending=Min('created_at'),
            newest_pending=Max('created_at')
        )
        
        # Calculer le temps d'attente moyen
        if pending_reviews.exists():
            from django.utils import timezone
            total_waiting_time = 0
            for review in pending_reviews:
                wait_time = (timezone.now() - review.created_at).days
                total_waiting_time += wait_time
            
            avg_waiting_time = total_waiting_time / pending_reviews.count()
        else:
            avg_waiting_time = 0
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        start = (page - 1) * page_size
        end = start + page_size
        
        paginated_reviews = pending_reviews[start:end]
        
        serializer = SellerReviewSerializer(
            paginated_reviews, 
            many=True, 
            context={'request': request}
        )
        
        # Catégoriser par priorité
        prioritized_reviews = []
        for review_data in serializer.data:
            review = pending_reviews.get(id=review_data['id'])
            
            # Déterminer la priorité
            priority = self._calculate_priority(review)
            
            review_data_with_priority = review_data.copy()
            review_data_with_priority['priority'] = priority
            review_data_with_priority['waiting_days'] = self._calculate_waiting_days(review)
            
            prioritized_reviews.append(review_data_with_priority)
        
        # Trier par priorité
        prioritized_reviews.sort(key=lambda x: (x['priority'], x['waiting_days']), reverse=True)
        
        return Response({
            'seller': {
                'id': request.user.id,
                'shop_name': getattr(request.user.vendor_profile, 'shop_name', request.user.get_full_name),
                'response_rate': self._calculate_response_rate(request.user)
            },
            'stats': {
                'total_pending': stats['total_pending'] or 0,
                'average_pending_rating': round(stats['average_rating'] or 0, 1),
                'avg_waiting_days': round(avg_waiting_time, 1),
                'oldest_pending': stats['oldest_pending'],
                'newest_pending': stats['newest_pending'],
                'by_rating': self._group_by_rating(pending_reviews)
            },
            'priority_summary': {
                'high': len([r for r in prioritized_reviews if r['priority'] == 'high']),
                'medium': len([r for r in prioritized_reviews if r['priority'] == 'medium']),
                'low': len([r for r in prioritized_reviews if r['priority'] == 'low'])
            },
            'reviews': prioritized_reviews,
            'suggested_responses': self._get_suggested_responses(),
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_reviews': pending_reviews.count(),
                'total_pages': (pending_reviews.count() + page_size - 1) // page_size,
                'has_next': end < pending_reviews.count(),
                'has_previous': page > 1
            }
        })
    
    def _calculate_priority(self, review):
        """Calculer la priorité d'un avis en attente"""
        from django.utils import timezone
        
        # Critères de priorité
        waiting_days = (timezone.now() - review.created_at).days
        
        if review.rating <= 2:  # Avis négatifs = haute priorité
            return 'high'
        elif waiting_days > 7:  # En attente depuis plus d'une semaine
            return 'high'
        elif review.is_verified_purchase:  # Achat vérifié
            return 'medium'
        else:
            return 'low'
    
    def _calculate_waiting_days(self, review):
        """Calculer le nombre de jours d'attente"""
        from django.utils import timezone
        return (timezone.now() - review.created_at).days
    
    def _calculate_response_rate(self, seller):
        """Calculer le taux de réponse"""
        total_reviews = Review.objects.filter(
            reviewed=seller,
            review_type='product'
        ).count()
        
        replied_reviews = Review.objects.filter(
            reviewed=seller,
            review_type='product',
            seller_reply__isnull=False
        ).count()
        
        if total_reviews > 0:
            return round((replied_reviews / total_reviews) * 100, 1)
        return 0
    
    def _group_by_rating(self, reviews):
        """Grouper les avis par note"""
        rating_groups = {}
        for rating in range(1, 6):
            rating_groups[rating] = reviews.filter(rating=rating).count()
        return rating_groups
    
    def _get_suggested_responses(self):
        """Retourner des réponses suggérées"""
        return [
            {
                'id': 1,
                'template': "Merci beaucoup pour votre avis ! Nous sommes ravis que vous soyez satisfait(e) de votre achat.",
                'for_rating': [4, 5]
            },
            {
                'id': 2,
                'template': "Merci pour votre retour. Nous prenons note de vos commentaires pour améliorer nos produits et services.",
                'for_rating': [3]
            },
            {
                'id': 3,
                'template': "Nous sommes désolés que votre expérience n'ait pas été à la hauteur de vos attentes. Pourriez-vous nous contacter pour que nous puissions résoudre ce problème ?",
                'for_rating': [1, 2]
            }
        ]
    
class SellerNegativeReviewsView(APIView):
    """
    Avis négatifs (1-3 étoiles) pour analyse des problèmes
    GET /api/reviews/seller/negative-reviews/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not request.user.is_seller:
            return Response({'error': 'Accès réservé'}, status=403)
        
        negative_reviews = Review.objects.filter(
            reviewed=request.user,
            review_type='product',
            rating__in=[1, 2, 3]
        ).order_by('-created_at')
        
        # Analyse des problèmes récurrents
        issues = self._analyze_issues(negative_reviews)
        
        return Response({
            'stats': {
                'total_negative': negative_reviews.count(),
                'average_negative_rating': negative_reviews.aggregate(avg=Avg('rating'))['avg'] or 0,
                'common_issues': issues
            },
            'reviews': SellerReviewSerializer(negative_reviews, many=True, context={'request': request}).data
        })
    
class SellerResponseHistoryView(APIView):
    """
    Historique des réponses données par le vendeur
    GET /api/reviews/seller/response-history/
    """
    def get(self, request):
        if not request.user.is_seller:
            return Response({'error': 'Accès réservé'}, status=403)
        
        replied_reviews = Review.objects.filter(
            reviewed=request.user,
            review_type='product',
            seller_reply__isnull=False
        ).order_by('-reply_date')
        
        # Analyse des temps de réponse
        response_times = []
        for review in replied_reviews:
            if review.reply_date:
                response_time = (review.reply_date - review.created_at).days
                response_times.append(response_time)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return Response({
            'stats': {
                'total_replied': replied_reviews.count(),
                'avg_response_days': round(avg_response_time, 1),
                'recent_responses': replied_reviews.filter(
                    reply_date__gte=timezone.now() - timedelta(days=30)
                ).count()
            },
            'history': SellerReviewSerializer(replied_reviews, many=True, context={'request': request}).data
        })
    
class SellerReviewAnalyticsView(APIView):
    """
    Analytics détaillées pour le vendeur
    GET /api/reviews/seller/analytics/
    """
    def get(self, request):
        from datetime import timedelta
        from django.utils import timezone
        from django.db.models.functions import TruncMonth, TruncWeek
        
        if not request.user.is_seller:
            return Response({'error': 'Accès réservé'}, status=403)
        
        reviews = Review.objects.filter(
            reviewed=request.user,
            review_type='product'
        )
        
        # Tendances mensuelles
        monthly_trends = reviews.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id'),
            avg_rating=Avg('rating')
        ).order_by('month')
        
        # Comparaison avec les autres vendeurs (simplifiée)
        all_sellers_avg = Review.objects.filter(
            review_type='product'
        ).aggregate(avg=Avg('rating'))['avg'] or 0
        
        return Response({
            'seller_performance': {
                'rating_vs_platform': round((reviews.aggregate(avg=Avg('rating'))['avg'] or 0) - all_sellers_avg, 1),
                'response_rate_vs_platform': 25.5,  # À calculer
                'ranking': 'Top 10%'  # À calculer
            },
            'monthly_trends': list(monthly_trends),
            'improvement_areas': self._get_improvement_suggestions(reviews)
        })
    


class AdminReviewsDashboardView(APIView):
    """
    Dashboard des avis pour l'administrateur
    GET /api/reviews/admin/dashboard/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Vérifier que l'utilisateur est admin
        if not request.user.is_staff and not request.user.is_superuser:
            return Response(
                {'error': 'Accès réservé aux administrateurs'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # RÉIMPORTER explicitement les fonctions d'agrégation
        from django.db.models import Count, Avg, Q
        
        # Récupérer tous les avis
        all_reviews = Review.objects.all()
        
        # Statistiques globales - UTILISEZ LES FONCTIONS RÉIMPORTÉES
        global_stats = all_reviews.aggregate(
            total_reviews=Count('id'),
            average_rating=Avg('rating'),
            verified_purchases=Count('id', filter=Q(is_verified_purchase=True))
        )
        
        # Statistiques par type
        by_type = {}
        for review_type in ['product', 'seller', 'buyer', 'platform']:
            reviews_by_type = all_reviews.filter(review_type=review_type)
            by_type[review_type] = {
                'count': reviews_by_type.count(),
                'average_rating': reviews_by_type.aggregate(avg=Avg('rating'))['avg'] or 0,
                'verified_purchases': reviews_by_type.filter(is_verified_purchase=True).count()
            }
        
        # Distribution des notes globale
        rating_distribution = {}
        for rating in range(1, 6):
            rating_distribution[rating] = all_reviews.filter(rating=rating).count()
        
        # Top des vendeurs par note
        top_sellers = []
        seller_reviews = all_reviews.filter(review_type='product')
        if seller_reviews.exists():
            top_sellers = User.objects.filter(
                is_seller=True,
                received_reviews__isnull=False
            ).annotate(
                avg_rating=Avg('received_reviews__rating'),
                total_reviews=Count('received_reviews')
            ).filter(
                total_reviews__gte=1
            ).order_by('-avg_rating')[:10]
            
            top_sellers_data = []
            for seller in top_sellers:
                top_sellers_data.append({
                    'id': seller.id,
                    'shop_name': getattr(seller.vendor_profile, 'shop_name', seller.get_full_name),
                    'average_rating': round(seller.avg_rating or 0, 1),
                    'total_reviews': seller.total_reviews or 0,
                    'avatar': seller.avatar.url if seller.avatar else None
                })
        else:
            top_sellers_data = []
        
        # Avis récents (7 derniers jours)
        from django.utils import timezone
        from datetime import timedelta
        last_7_days = timezone.now() - timedelta(days=7)
        recent_reviews = all_reviews.filter(created_at__gte=last_7_days).count()
        
        # Avis en attente de réponse (tous vendeurs confondus)
        pending_replies = all_reviews.filter(
            review_type='product',
            seller_reply__isnull=True
        ).count()
        
        # Avis avec réponse (pourcentage)
        replied_reviews = all_reviews.filter(
            review_type='product',
            seller_reply__isnull=False
        ).count()
        total_product_reviews = all_reviews.filter(review_type='product').count()
        response_rate = (replied_reviews / total_product_reviews * 100) if total_product_reviews > 0 else 0
        
        # Tendances
        trends = self._get_trends(all_reviews)
        
        return Response({
            'admin': {
                'id': request.user.id,
                'email': request.user.email,
                'name': request.user.get_full_name
            },
            'global_stats': {
                'total_reviews': global_stats['total_reviews'] or 0,
                'average_rating': round(global_stats['average_rating'] or 0, 2),
                'verified_purchases': global_stats['verified_purchases'] or 0,
                'verified_percentage': (
                    (global_stats['verified_purchases'] / global_stats['total_reviews'] * 100)
                    if global_stats['total_reviews'] > 0 else 0
                ),
                'recent_reviews': recent_reviews,
                'pending_replies': pending_replies,
                'response_rate': round(response_rate, 1)
            },
            'by_type': by_type,
            'rating_distribution': rating_distribution,
            'top_sellers': top_sellers_data,
            'trends': trends
        })
    
    def _get_trends(self, reviews):
        """Calculer les tendances sur 30 jours"""
        from django.db.models import Count, Avg
        from django.db.models.functions import TruncDate
        from django.utils import timezone
        from datetime import timedelta
        
        # Données des 30 derniers jours
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_reviews = reviews.filter(created_at__gte=thirty_days_ago)
        
        # Agrégation par jour
        daily_stats = recent_reviews.annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id'),
            avg_rating=Avg('rating')
        ).order_by('date')
        
        # Calculer la tendance
        daily_stats_list = list(daily_stats)
        if len(daily_stats_list) >= 2:
            first_day = daily_stats_list[0]
            last_day = daily_stats_list[-1]
            trend = {
                'daily_change': round((last_day['count'] - first_day['count']) / len(daily_stats_list), 1),
                'rating_change': round((last_day['avg_rating'] - first_day['avg_rating']), 2),
                'direction': 'up' if last_day['count'] > first_day['count'] else 'down'
            }
        else:
            trend = {
                'daily_change': 0,
                'rating_change': 0,
                'direction': 'stable'
            }
        
        return {
            'daily_stats': daily_stats_list,
            'trend': trend
        } 

class AdminAllReviewsView(APIView):
    """
    Tous les avis pour l'admin avec filtres
    GET /api/reviews/admin/all/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Vérifier que l'utilisateur est admin
        if not request.user.is_staff and not request.user.is_superuser:
            return Response(
                {'error': 'Accès réservé aux administrateurs'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Récupérer tous les avis avec filtres
        reviews = Review.objects.all().order_by('-created_at')
        
        # Appliquer les filtres
        review_type = request.query_params.get('type')
        if review_type:
            reviews = reviews.filter(review_type=review_type)
        
        rating = request.query_params.get('rating')
        if rating:
            reviews = reviews.filter(rating=rating)
        
        verified = request.query_params.get('verified')
        if verified:
            reviews = reviews.filter(is_verified_purchase=verified.lower() == 'true')
        
        has_reply = request.query_params.get('has_reply')
        if has_reply:
            if has_reply.lower() == 'true':
                reviews = reviews.filter(seller_reply__isnull=False)
            else:
                reviews = reviews.filter(seller_reply__isnull=True)
        
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        if date_from:
            reviews = reviews.filter(created_at__gte=date_from)
        if date_to:
            reviews = reviews.filter(created_at__lte=date_to)
        
        search = request.query_params.get('search')
        if search:
            reviews = reviews.filter(
                Q(comment__icontains=search) |
                Q(reviewer__email__icontains=search) |
                Q(reviewer__first_name__icontains=search) |
                Q(reviewer__last_name__icontains=search) |
                Q(reviewed__email__icontains=search) |
                Q(reviewed__first_name__icontains=search) |
                Q(reviewed__last_name__icontains=search)
            )
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        
        total_reviews = reviews.count()
        paginated_reviews = reviews[start:end]
        
        serializer = ReviewSerializer(paginated_reviews, many=True, context={'request': request})
        
        # Statistiques des filtres actuels
        stats = reviews.aggregate(
            total=Count('id'),
            average_rating=Avg('rating'),
            verified_count=Count('id', filter=Q(is_verified_purchase=True))
        )
        
        return Response({
            'filters': {
                'type': review_type,
                'rating': rating,
                'verified': verified,
                'has_reply': has_reply,
                'date_from': date_from,
                'date_to': date_to,
                'search': search
            },
            'stats': {
                'total': stats['total'] or 0,
                'average_rating': round(stats['average_rating'] or 0, 1),
                'verified_percentage': (
                    (stats['verified_count'] / stats['total'] * 100)
                    if stats['total'] > 0 else 0
                )
            },
            'reviews': serializer.data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total_reviews,
                'total_pages': (total_reviews + page_size - 1) // page_size,
                'has_next': end < total_reviews,
                'has_previous': page > 1
            }
        })
    

class AdminReviewModerationView(APIView):
    """
    Modération des avis pour l'admin
    POST /api/reviews/admin/moderate/<int:review_id>/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, review_id):
        # Vérifier que l'utilisateur est admin
        if not request.user.is_staff and not request.user.is_superuser:
            return Response(
                {'error': 'Accès réservé aux administrateurs'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            review = Review.objects.get(id=review_id)
        except Review.DoesNotExist:
            return Response(
                {'error': 'Avis non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        action = request.data.get('action')
        reason = request.data.get('reason', '')
        
        if action == 'delete':
            # Supprimer l'avis
            review_id = review.id
            reviewer_email = review.reviewer.email
            review.delete()
            
            # Mettre à jour les statistiques
            if review.reviewed:
                
                stats = Review.objects.filter(reviewed=review.reviewed).aggregate(
                    avg_rating=Avg('rating'),
                    total_reviews=Count('id')
                )
                review.reviewed.average_rating = stats['avg_rating'] or 0
                review.reviewed.total_reviews = stats['total_reviews'] or 0
                review.reviewed.save()
            
            return Response({
                'message': 'Avis supprimé avec succès',
                'review_id': review_id,
                'reviewer': reviewer_email,
                'action': 'deleted',
                'reason': reason
            })
        
        elif action == 'hide':
            # Masquer l'avis (marquer comme inapproprié)
            review.is_hidden = True
            review.hidden_reason = reason
            review.hidden_by = request.user
            review.hidden_at = timezone.now()
            review.save()
            
            return Response({
                'message': 'Avis masqué avec succès',
                'review_id': review.id,
                'action': 'hidden',
                'reason': reason
            })
        
        elif action == 'unhide':
            # Restaurer un avis masqué
            review.is_hidden = False
            review.hidden_reason = None
            review.hidden_by = None
            review.hidden_at = None
            review.save()
            
            return Response({
                'message': 'Avis restauré avec succès',
                'review_id': review.id,
                'action': 'unhidden'
            })
        
        else:
            return Response(
                {'error': 'Action non valide. Options: delete, hide, unhide'},
                status=status.HTTP_400_BAD_REQUEST
            )
        

class AdminPlatformAnalyticsView(APIView):
    """
    Analytics détaillés pour l'admin
    GET /api/reviews/admin/platform-analytics/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Vérifier que l'utilisateur est admin
        if not request.user.is_staff and not request.user.is_superuser:
            return Response(
                {'error': 'Accès réservé aux administrateurs'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Récupérer tous les avis
        all_reviews = Review.objects.all()
        
        # 1. Performance globale
        global_stats = self._get_global_stats(all_reviews)
        
        # 2. Performance par type
        type_stats = self._get_type_stats(all_reviews)
        
        # 3. Tendances temporelles
        time_trends = self._get_time_trends(all_reviews)
        
        # 4. Top performers
        top_performers = self._get_top_performers(all_reviews)
        
        # 5. Problèmes fréquents
        common_issues = self._get_common_issues(all_reviews)
        
        return Response({
            'global_performance': global_stats,
            'by_type': type_stats,
            'time_trends': time_trends,
            'top_performers': top_performers,
            'common_issues': common_issues,
            'recommendations': self._get_recommendations(global_stats, type_stats, common_issues)
        })
    
    def _get_global_stats(self, reviews):
        stats = reviews.aggregate(
            total=Count('id'),
            avg_rating=Avg('rating'),
            verified_count=Count('id', filter=Q(is_verified_purchase=True)),
            helpful_total=Sum('helpful_count'),
            not_helpful_total=Sum('not_helpful_count')
        )
        
        total_reviews = stats['total'] or 0
        avg_rating = stats['avg_rating'] or 0
        
        # Distribution des notes
        rating_dist = {}
        for rating in range(1, 6):
            rating_dist[rating] = reviews.filter(rating=rating).count()
        
        # Pourcentages
        verified_percentage = (stats['verified_count'] / total_reviews * 100) if total_reviews > 0 else 0
        
        # Score d'utilité
        helpful_total = stats['helpful_total'] or 0
        not_helpful_total = stats['not_helpful_total'] or 0
        helpful_percentage = (helpful_total / (helpful_total + not_helpful_total) * 100) if (helpful_total + not_helpful_total) > 0 else 0
        
        return {
            'total_reviews': total_reviews,
            'average_rating': round(avg_rating, 2),
            'verified_percentage': round(verified_percentage, 1),
            'helpful_percentage': round(helpful_percentage, 1),
            'rating_distribution': rating_dist,
            'star_rating': self._get_star_rating(avg_rating)
        }
    
    def _get_type_stats(self, reviews):
        types = ['product', 'seller', 'buyer', 'platform']
        result = {}
        
        for t in types:
            type_reviews = reviews.filter(review_type=t)
            stats = type_reviews.aggregate(
                count=Count('id'),
                avg_rating=Avg('rating'),
                verified=Count('id', filter=Q(is_verified_purchase=True))
            )
            
            result[t] = {
                'count': stats['count'] or 0,
                'average_rating': round(stats['avg_rating'] or 0, 2),
                'verified_count': stats['verified'] or 0,
                'percentage_of_total': round((stats['count'] / reviews.count() * 100), 1) if reviews.count() > 0 else 0
            }
        
        return result
    
    def _get_time_trends(self, reviews):
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models.functions import TruncMonth, TruncWeek
        
        # Tendances mensuelles
        monthly = reviews.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id'),
            avg_rating=Avg('rating')
        ).order_by('month')[-12:]  # 12 derniers mois
        
        # Tendances hebdomadaires (8 dernières semaines)
        eight_weeks_ago = timezone.now() - timedelta(weeks=8)
        weekly = reviews.filter(
            created_at__gte=eight_weeks_ago
        ).annotate(
            week=TruncWeek('created_at')
        ).values('week').annotate(
            count=Count('id'),
            avg_rating=Avg('rating')
        ).order_by('week')
        
        return {
            'monthly': list(monthly),
            'weekly': list(weekly),
            'current_month': reviews.filter(
                created_at__month=timezone.now().month,
                created_at__year=timezone.now().year
            ).count(),
            'previous_month': reviews.filter(
                created_at__month=(timezone.now().month - 1),
                created_at__year=timezone.now().year
            ).count() if timezone.now().month > 1 else 0
        }
    
    def _get_top_performers(self, reviews):
        # Top vendeurs
        from django.db.models import Avg, Count
        top_sellers = User.objects.filter(
            is_seller=True,
            received_reviews__isnull=False
        ).annotate(
            avg_rating=Avg('received_reviews__rating'),
            total_reviews=Count('received_reviews'),
            response_rate=self._calculate_response_rate_annotation()
        ).filter(
            total_reviews__gte=5
        ).order_by('-avg_rating')[:10]
        
        sellers_data = []
        for seller in top_sellers:
            sellers_data.append({
                'id': seller.id,
                'name': seller.get_full_name,
                'shop_name': getattr(seller.vendor_profile, 'shop_name', ''),
                'average_rating': round(seller.avg_rating or 0, 1),
                'total_reviews': seller.total_reviews or 0,
                'response_rate': seller.response_rate or 0,
                'avatar': seller.avatar.url if seller.avatar else None
            })
        
        # Top produits (si vous avez un modèle Listing)
        try:
            from listings.models import Listing
            top_listings = Listing.objects.annotate(
                avg_rating=Avg('reviews__rating'),
                review_count=Count('reviews')
            ).filter(
                review_count__gte=3
            ).order_by('-avg_rating')[:10]
            
            listings_data = []
            for listing in top_listings:
                listings_data.append({
                    'id': listing.id,
                    'title': listing.title,
                    'seller': listing.user.get_full_name,
                    'average_rating': round(listing.avg_rating or 0, 1),
                    'review_count': listing.review_count or 0,
                    'price': float(listing.price) if listing.price else 0
                })
        except:
            listings_data = []
        
        return {
            'top_sellers': sellers_data,
            'top_listings': listings_data
        }
    
    def _calculate_response_rate_annotation(self):
        from django.db.models import Case, When, Value, IntegerField, Count, Q
        from django.db.models.functions import Cast
        
        return Cast(
            Count(Case(
                When(
                    Q(received_reviews__seller_reply__isnull=False),
                    then=Value(1)
                ),
                output_field=IntegerField()
            )) * 100 / Count('received_reviews'),
            IntegerField()
        )
    
    def _get_common_issues(self, reviews):
        # Avis négatifs (1-3 étoiles)
        negative_reviews = reviews.filter(rating__in=[1, 2, 3])
        
        if not negative_reviews.exists():
            return []
        
        # Analyser les mots-clés dans les commentaires négatifs
        import re
        from collections import Counter
        
        all_comments = " ".join([r.comment.lower() for r in negative_reviews])
        
        # Supprimer les mots vides (stop words en français)
        stop_words = {'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou', 'à', 'au', 'aux', 
                     'pour', 'dans', 'sur', 'avec', 'sans', 'par', 'mais', 'donc', 'or', 'ni', 'car',
                     'je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils', 'elles', 'mon', 'ton', 'son',
                     'notre', 'votre', 'leur', 'ce', 'cet', 'cette', 'ces', 'ne', 'pas', 'très'}
        
        words = re.findall(r'\b\w{4,}\b', all_comments)  # Mots de 4+ lettres
        filtered_words = [word for word in words if word not in stop_words]
        
        word_counts = Counter(filtered_words).most_common(10)
        
        # Catégoriser les problèmes
        categories = {
            'livraison': ['livraison', 'livré', 'retard', 'délai', 'colis', 'expédition'],
            'produit': ['produit', 'qualité', 'défaut', 'cassé', 'endommagé', 'conforme'],
            'service': ['service', 'client', 'réponse', 'contact', 'support', 'aide'],
            'emballage': ['emballage', 'protégé', 'abîmé', 'sous'],
            'communication': ['communication', 'réponse', 'contact', 'message', 'appel']
        }
        
        categorized = {}
        for category, keywords in categories.items():
            category_count = sum(1 for word in filtered_words if word in keywords)
            if category_count > 0:
                categorized[category] = {
                    'count': category_count,
                    'percentage': round((category_count / len(filtered_words) * 100), 1)
                }
        
        return {
            'total_negative': negative_reviews.count(),
            'common_words': [{'word': word, 'count': count} for word, count in word_counts],
            'categories': categorized,
            'sample_reviews': ReviewSerializer(
                negative_reviews.order_by('-created_at')[:5], 
                many=True, 
                context={'request': self.request}
            ).data
        }
    
    def _get_star_rating(self, rating):
        stars = '★★★★★'
        filled = int(rating)
        return stars[:filled] + '☆☆☆☆☆'[filled:]
    
    def _get_recommendations(self, global_stats, type_stats, common_issues):
        recommendations = []
        
        # Recommandation basée sur le taux de réponse
        if 'product' in type_stats:
            product_stats = type_stats['product']
            if product_stats['count'] > 0:
                response_rate = self._calculate_response_rate_for_type('product')
                if response_rate < 50:
                    recommendations.append({
                        'priority': 'medium',
                        'title': 'Améliorer le taux de réponse des vendeurs',
                        'description': f'Seulement {response_rate}% des avis sur les produits reçoivent une réponse.',
                        'action': 'Mettre en place un système de rappel pour les vendeurs'
                    })
        
        # Recommandation basée sur les avis négatifs
        if common_issues.get('total_negative', 0) > 0:
            negative_percentage = (common_issues['total_negative'] / global_stats['total_reviews'] * 100)
            if negative_percentage > 15:
                recommendations.append({
                    'priority': 'high',
                    'title': 'Réduire le nombre d\'avis négatifs',
                    'description': f'{round(negative_percentage, 1)}% des avis sont négatifs (1-3 étoiles).',
                    'action': 'Analyser les causes principales et implémenter des solutions'
                })
        
        # Recommandation basée sur la distribution des notes
        rating_dist = global_stats.get('rating_distribution', {})
        if rating_dist.get(1, 0) + rating_dist.get(2, 0) > rating_dist.get(5, 0):
            recommendations.append({
                'priority': 'high',
                'title': 'Augmenter la satisfaction client',
                'description': 'Plus d\'avis négatifs que d\'avis très positifs.',
                'action': 'Mettre en place un programme de satisfaction client'
            })
        
        return recommendations
    
    def _calculate_response_rate_for_type(self, review_type):

        reviews = Review.objects.filter(review_type=review_type)
        total = reviews.count()
        responded = reviews.filter(seller_reply__isnull=False).count()
        return round((responded / total * 100), 1) if total > 0 else 0
    

class AdminUserReviewsView(APIView):
    """
    Avis pour un utilisateur spécifique (admin view)
    GET /api/reviews/admin/user/<int:user_id>/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id):
        # Vérifier que l'utilisateur est admin
        if not request.user.is_staff and not request.user.is_superuser:
            return Response(
                {'error': 'Accès réservé aux administrateurs'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'Utilisateur non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Avis donnés par l'utilisateur
        given_reviews = Review.objects.filter(reviewer=user).order_by('-created_at')
        
        # Avis reçus par l'utilisateur
        received_reviews = Review.objects.filter(reviewed=user).order_by('-created_at')
        
        # Statistiques complètes
        given_stats = given_reviews.aggregate(
            total_given=Count('id'),
            avg_given_rating=Avg('rating'),
            helpful_total=Sum('helpful_count'),
            verified_given=Count('id', filter=Q(is_verified_purchase=True))
        )
        
        received_stats = received_reviews.aggregate(
            total_received=Count('id'),
            avg_received_rating=Avg('rating'),
            response_rate=(
                Count('id', filter=Q(seller_reply__isnull=False)) / Count('id') * 100
                if Count('id') > 0 else 0
            )
        )
        
        # Distribution des notes données
        given_distribution = {}
        for rating in range(1, 6):
            given_distribution[rating] = given_reviews.filter(rating=rating).count()
        
        # Distribution des notes reçues
        received_distribution = {}
        for rating in range(1, 6):
            received_distribution[rating] = received_reviews.filter(rating=rating).count()
        
        # Types d'avis donnés
        given_by_type = {}
        for review_type in ['product', 'seller', 'buyer', 'platform']:
            given_by_type[review_type] = given_reviews.filter(review_type=review_type).count()
        
        return Response({
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.get_full_name,
                'is_seller': user.is_seller,
                'is_active': user.is_active,
                'created_at': user.created_at
            },
            'given_reviews': {
                'total': given_stats['total_given'] or 0,
                'average_rating': round(given_stats['avg_given_rating'] or 0, 1),
                'helpful_total': given_stats['helpful_total'] or 0,
                'verified_count': given_stats['verified_given'] or 0,
                'distribution': given_distribution,
                'by_type': given_by_type,
                'reviews': ReviewSerializer(given_reviews, many=True, context={'request': request}).data
            },
            'received_reviews': {
                'total': received_stats['total_received'] or 0,
                'average_rating': round(received_stats['avg_received_rating'] or 0, 1),
                'response_rate': round(received_stats['response_rate'] or 0, 1),
                'distribution': received_distribution,
                'reviews': ReviewSerializer(received_reviews, many=True, context={'request': request}).data
            }
        })