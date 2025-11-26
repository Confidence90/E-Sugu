#managers.py
from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import make_password

class UserManager(BaseUserManager):
    def create_user(self, email,first_name, last_name, phone, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est requise")
        if not phone:
            raise ValueError("Le numéro de téléphone est requis")

        email = self.normalize_email(email)
        role = extra_fields.get('role', 'buyer')
        if role == 'seller':
            extra_fields.setdefault('is_seller', True)
            extra_fields.setdefault('is_seller_pending', True)
        else:
            extra_fields.setdefault('is_seller', False)
            extra_fields.setdefault('is_seller_pending', False)
        user = self.model(
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        **extra_fields
        )
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email,first_name, last_name, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_seller', False)
        extra_fields.setdefault('is_seller_pending', False)

        if not extra_fields.get('is_staff'):
            raise ValueError('Le superutilisateur doit avoir is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Le superutilisateur doit avoir is_superuser=True.')

        if self.model.objects.filter(phone=phone).exists():
            raise ValueError("Un utilisateur avec ce numéro existe déjà.")

        user = self.create_user(email, first_name, last_name, phone, password=password, **extra_fields)
        return user
        

    def email_validator(self, email):
        try: 
            validate_email(email)
        except ValidationError:
            raise ValueError(_("Veuillez saisir un email correct"))
