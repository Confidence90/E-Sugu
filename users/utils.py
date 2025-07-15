import random
from datetime import timedelta
from django.utils import timezone
from django.core.mail import EmailMessage
from django.conf import settings
from .models import OneTimePassword, User
from google.auth.transport import requests
from rest_framework_simplejwt.tokens import RefreshToken
from google.oauth2 import id_token
from django.contrib.auth import authenticate
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed


class Google():
    @staticmethod
    def validate(access_token):
        try:
            id_info = id_token.verify_oauth2_token(access_token, requests.Request())
            if "accounts.google.com" in id_info['iss']: 
                return id_info
        except Exception:
            return "Le token est invalide ou expiré"

def login_user(email, password):
    user = authenticate(email=email, password=password)
    if not user:
        raise AuthenticationFailed("Identifiants invalides.")
    refresh = RefreshToken.for_user(user)
    return {
        'email': user.email,
        'full_name': user.get_full_name(),
        'access_token': str(refresh.access_token),
        'refresh_token': str(refresh),
    }

def register_social_user(provider, email, first_name, last_name):
    user = User.objects.filter(email=email)
    if user.exists():
        if provider == user[0].auth_provider:
            return login_user(email, settings.SOCIAL_AUTH_PASSWORD)
        else:
            raise AuthenticationFailed(
                detail=f"Veuillez continuer votre connexion avec {user[0].auth_provider}"
            )
    else:
        new_user = {
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'password': settings.SOCIAL_AUTH_PASSWORD
        }
        register_user = User.objects.create_user(**new_user)
        register_user.auth_provider = provider
        register_user.is_verified = True
        register_user.save()
        return login_user(email=register_user.email, password=settings.SOCIAL_AUTH_PASSWORD)


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
