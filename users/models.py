from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken


class UserManager(BaseUserManager):
    def create_user(self, email, phone, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est requise")
        if not phone:
            raise ValueError("Le numéro de téléphone est requis")

        email = self.normalize_email(email)
        user = self.model(email=email, phone=phone, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if not extra_fields.get('is_staff'):
            raise ValueError('Le superutilisateur doit avoir is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Le superutilisateur doit avoir is_superuser=True.')

        return self.create_user(email, phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('buyer', 'Acheteur'),
        ('seller', 'Vendeur'),
        ('admin', 'Administrateur'),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, null=True, blank=True)
    country_code = models.CharField(max_length=10)
    phone = models.CharField(max_length=15, unique=True)
    phone_full = models.CharField(max_length=25, unique=True)
    password = models.CharField(max_length=128)
    location = models.CharField(max_length=100, null=True, blank=True)
    stripe_account_id = models.CharField(max_length=255, null=True, blank=True)

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='buyer')

    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone']

    def __str__(self):
        return f"{self.name or self.email}"

    def get_token(self):
        refresh = RefreshToken.for_user(self)
        return str(refresh.access_token)
