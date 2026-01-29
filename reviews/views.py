# reviews/views.py - AJOUTEZ ces vues
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status, generics
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Count, Q
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from .models import Review
from .serializers import (
    ReviewSerializer, 
    CreateReviewSerializer,
    PlatformReviewCreateSerializer,
    ReplySerializer,
    VoteSerializer
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