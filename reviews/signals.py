# reviews/signals.py
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.conf import settings
from users.models import User
import logging
from django.db.models import  Q

logger = logging.getLogger(__name__)

@receiver(post_migrate)
def ensure_platform_admin_exists(sender, **kwargs):
    """S'assurer qu'il y a toujours un admin pour les avis plateforme"""
    if sender.name == 'reviews':
        # Vérifier si un admin existe déjà
        admin_user = User.objects.filter(
            Q(is_superuser=True) | Q(is_staff=True) | Q(role='admin')
        ).first()
        
        if not admin_user:
            logger.warning("⚠️ Aucun administrateur trouvé pour les avis plateforme.")
            logger.warning("   Créez un superutilisateur ou admin via: python manage.py createsuperuser")
        
        # Créer un utilisateur spécial si aucun admin n'existe
        if not admin_user and getattr(settings, 'AUTO_CREATE_PLATFORM_USER', False):
            try:
                admin_user = User.objects.create(
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
                admin_user.set_unusable_password()
                admin_user.save()
                logger.info("✅ Utilisateur plateforme créé automatiquement")
            except Exception as e:
                logger.error(f"❌ Erreur création utilisateur plateforme: {e}")

# __init__.py
default_app_config = 'reviews.apps.ReviewsConfig'