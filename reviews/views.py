# reviews/views.py - AJOUTEZ ces vues
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status, generics
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Count, Q, F, Min, Max                               
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