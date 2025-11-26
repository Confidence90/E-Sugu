import random
from datetime import timedelta
from django.utils import timezone
from django.core.mail import EmailMessage
from django.conf import settings
from .models import OneTimePassword, User
from google.auth.transport import requests
from rest_framework_simplejwt.tokens import RefreshToken
from google.oauth2 import id_token
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed
import logging

logger = logging.getLogger(__name__)




# 🔐 Générer un OTP à 6 chiffres (aléatoire, pas TOTP)
def generate_otp(length=6):
    return ''.join(str(random.randint(0, 9)) for _ in range(length))

# 📩 Envoyer le code OTP par e-mail
def send_otp_email(user, code):
    subject = "✅ Votre code de vérification"
    from_email = settings.DEFAULT_FROM_EMAIL
    site_name = "E-sugu"  # Tu peux rendre ça dynamique avec settings.SITE_NAME si tu veux

    message = f"""
Bonjour {user.first_name},

Voici votre code de vérification : {code}

Ce code est valable pendant 5 minutes. Ne le communiquez à personne.

Merci,
L’équipe {site_name}
    """

    email = EmailMessage(subject, message, from_email, [user.email])
    email.send(fail_silently=False)

# 🧠 Assigner un OTP à un utilisateur (supprime l’ancien s’il existe)
def assign_otp_to_user(user):
    OneTimePassword.objects.filter(user=user).delete()
    code = generate_otp()
    OneTimePassword.objects.create(user=user, code=code)
    return code

# ✅ Vérifier le code OTP soumis
def verify_otp(user, input_code):
    try:
        otp_obj = OneTimePassword.objects.get(user=user)
    except OneTimePassword.DoesNotExist:
        return False, "Aucun code OTP trouvé"

    delta = timezone.now() - otp_obj.created_at
    if delta.total_seconds() > 300:
        return False, "Code expiré"

    if otp_obj.code != input_code:
        return False, "Code incorrect"

    otp_obj.delete()  # Supprime après succès
    return True, "Code vérifié avec succès"


def send_normal_email(data):
    email = EmailMessage(
        subject=data['email_subject'],
        body=data['email_body'],
        from_email=settings.EMAIL_HOST_USER,  # ✅ Spécifie l'expéditeur
        to=[data['to_email']]
    )
    email.send(fail_silently=False)  # ✅ Affiche les erreurs d’envoi
def send_password_reset_email(user, reset_url):
    subject = "🔐 Réinitialisation de votre mot de passe E-Sugu"
    from_email = settings.DEFAULT_FROM_EMAIL
    site_name = "E-sugu" 
    message = f"""
Bonjour {user.first_name},

Vous avez demandé la réinitialisation de votre mot de passe E-Sugu.

🔄 **CLIQUEZ SUR LE LIEN SUIVANT :**
{reset_url}

⏰ Ce lien expirera dans 24 heures.

🔒 **Sécurité importante :**
- Ne partagez jamais ce lien
- Si vous n'avez pas fait cette demande, ignorez cet email
- Contactez notre support en cas de doute

Merci de nous aider à garder votre compte sécurisé.

Cordialement,
L'équipe {site_name}
    """

    # ✅ LOGGING DÉTAILLÉ
    logger.info(f"📧 send_password_reset_email appelée")
    logger.info(f"📧 Destinataire: {user.email}")
    logger.info(f"📧 Expéditeur: {from_email}")
    logger.info(f"📧 Sujet: {subject}")
    logger.info(f"📧 URL de reset: {reset_url}")

    try:
        email = EmailMessage(subject, message, from_email, [user.email])
        logger.info(f"📧 EmailMessage créé, envoi en cours...")
        email.send(fail_silently=False)
        logger.info(f"✅ Email envoyé avec succès à {user.email}")
        return True
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'envoi: {str(e)}", exc_info=True)
        return False