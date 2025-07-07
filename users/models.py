#models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from .managers import UserManager


COUNTRY_CHOICES = [
    # Afrique
    ('+213', 'Algérie (+213)'), ('+229', 'Bénin (+229)'), ('+226', 'Burkina Faso (+226)'), 
    ('+237', 'Cameroun (+237)'), ('+238', 'Cap-Vert (+238)'), ('+236', 'Centrafrique (+236)'), 
    ('+235', 'Tchad (+235)'), ('+269', 'Comores (+269)'), ('+242', 'Congo-Brazzaville (+242)'), 
    ('+243', 'RD Congo (+243)'), ('+225', 'Côte d’Ivoire (+225)'), ('+240', 'Guinée équatoriale (+240)'), 
    ('+241', 'Gabon (+241)'), ('+220', 'Gambie (+220)'), ('+233', 'Ghana (+233)'), 
    ('+224', 'Guinée (+224)'), ('+245', 'Guinée-Bissau (+245)'), ('+254', 'Kenya (+254)'), 
    ('+266', 'Lesotho (+266)'), ('+231', 'Libéria (+231)'), ('+218', 'Libye (+218)'), 
    ('+261', 'Madagascar (+261)'), ('+265', 'Malawi (+265)'), ('+223', 'Mali (+223)'), 
    ('+222', 'Mauritanie (+222)'), ('+230', 'Maurice (+230)'), ('+262', 'Mayotte (+262)'), 
    ('+212', 'Maroc (+212)'), ('+258', 'Mozambique (+258)'), ('+264', 'Namibie (+264)'), 
    ('+227', 'Niger (+227)'), ('+234', 'Nigéria (+234)'), ('+250', 'Rwanda (+250)'), 
    ('+239', 'Sao Tomé-et-Principe (+239)'), ('+221', 'Sénégal (+221)'), ('+248', 'Seychelles (+248)'), 
    ('+232', 'Sierra Leone (+232)'), ('+252', 'Somalie (+252)'), ('+27', 'Afrique du Sud (+27)'), 
    ('+211', 'Soudan du Sud (+211)'), ('+249', 'Soudan (+249)'), ('+255', 'Tanzanie (+255)'), 
    ('+228', 'Togo (+228)'), ('+216', 'Tunisie (+216)'), ('+256', 'Ouganda (+256)'), 
    ('+260', 'Zambie (+260)'), ('+263', 'Zimbabwe (+263)'),

    # Europe
    ('+43', 'Autriche (+43)'), ('+32', 'Belgique (+32)'), ('+359', 'Bulgarie (+359)'), 
    ('+385', 'Croatie (+385)'), ('+357', 'Chypre (+357)'), ('+420', 'République Tchèque (+420)'), 
    ('+45', 'Danemark (+45)'), ('+372', 'Estonie (+372)'), ('+358', 'Finlande (+358)'), 
    ('+33', 'France (+33)'), ('+49', 'Allemagne (+49)'), ('+30', 'Grèce (+30)'), 
    ('+36', 'Hongrie (+36)'), ('+353', 'Irlande (+353)'), ('+39', 'Italie (+39)'), 
    ('+371', 'Lettonie (+371)'), ('+370', 'Lituanie (+370)'), ('+352', 'Luxembourg (+352)'), 
    ('+31', 'Pays-Bas (+31)'), ('+48', 'Pologne (+48)'), ('+351', 'Portugal (+351)'), 
    ('+40', 'Roumanie (+40)'), ('+421', 'Slovaquie (+421)'), ('+386', 'Slovénie (+386)'), 
    ('+34', 'Espagne (+34)'), ('+46', 'Suède (+46)'), ('+41', 'Suisse (+41)'), 
    ('+44', 'Royaume-Uni (+44)'),

    # Asie
    ('+93', 'Afghanistan (+93)'), ('+880', 'Bangladesh (+880)'), ('+86', 'Chine (+86)'), 
    ('+91', 'Inde (+91)'), ('+62', 'Indonésie (+62)'), ('+81', 'Japon (+81)'), 
    ('+82', 'Corée du Sud (+82)'), ('+60', 'Malaisie (+60)'), ('+95', 'Myanmar (+95)'), 
    ('+92', 'Pakistan (+92)'), ('+63', 'Philippines (+63)'), ('+65', 'Singapour (+65)'), 
    ('+66', 'Thaïlande (+66)'), ('+84', 'Vietnam (+84)'),

    # Amériques
    ('+54', 'Argentine (+54)'), ('+55', 'Brésil (+55)'), ('+56', 'Chili (+56)'), 
    ('+57', 'Colombie (+57)'), ('+53', 'Cuba (+53)'), ('+593', 'Équateur (+593)'), 
    ('+502', 'Guatemala (+502)'), ('+504', 'Honduras (+504)'), ('+52', 'Mexique (+52)'), 
    ('+1', 'États-Unis (+1)'), ('+598', 'Uruguay (+598)'), ('+58', 'Venezuela (+58)'),

    # Océanie
    ('+61', 'Australie (+61)'), ('+64', 'Nouvelle-Zélande (+64)'), ('+675', 'Papouasie-Nouvelle-Guinée (+675)'),
    ]


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('buyer', 'Acheteur'),
        ('seller', 'Vendeur'),
        ('admin', 'Administrateur'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='buyer')
    first_name = models.CharField(max_length=100, verbose_name=_("Prenom"), default="", blank=True)
    last_name = models.CharField(max_length=100, verbose_name=_("Nom"), default="", blank=True)
    username = models.CharField("Nom d'utilisateur", max_length=100, unique=True, null=True)
    email = models.EmailField(unique=True, null=True, blank=True, verbose_name=_("Email"))
    country_code = models.CharField(max_length=4, choices=COUNTRY_CHOICES, default='+225', verbose_name="Indicatif pays")
    phone = models.CharField(max_length=15, unique=True)
    phone_full = models.CharField(max_length=25, unique=True)
    password = models.CharField(max_length=128)
    location = models.CharField(max_length=100, null=True, blank=True)
    stripe_account_id = models.CharField(max_length=255, null=True, blank=True)
    bio = models.CharField(max_length=100, blank=True, null=True)
    is_seller = models.BooleanField("Vendeur", default=False)
    is_seller_pending = models.BooleanField(default=False)
    is_active = models.BooleanField("En ligne", default=True)
    is_staff = models.BooleanField("Membre admin", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username', 'phone']

    def __str__(self):
        return f"{self.username or self.email}"
    @property
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_token(self):
        refresh = RefreshToken.for_user(self)
        return {
            'refresh': str(refresh),
            'access':str(refresh.access_token)}


class OneTimePassword(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        from django.utils import timezone
        return (timezone.now() - self.created_at).total_seconds() < 300

    def __str__(self):
        return f"{self.user.get_full_name()} - code"
