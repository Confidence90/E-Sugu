#models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.validators import RegexValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .managers import UserManager

REGION_CHOICES = [
        ('Bamako', 'Bamako'),
        ('Kayes', 'Kayes'),
        ('Koulikoro', 'Koulikoro'),
        ('Sikasso', 'Sikasso'),
        ('Ségou', 'Ségou'),
        ('Mopti', 'Mopti'),
        ('Tombouctou', 'Tombouctou'),
        ('Gao', 'Gao'),
        ('Kidal', 'Kidal'),
    ]
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
AUTH_PROVIDERS ={'email':'email', 'google':'google', 'github':'github', 'facebook':'facebook'}

# Status choices for vendor profile and verification
STATUS_CHOICES = [
    ('pending', 'En attente'),
    ('approved', 'Approuvé'),
    ('rejected', 'Rejeté'),
    ('suspended', 'Suspendu'),
]

VERIFICATION_STATUS_CHOICES = [
    ('pending', 'En attente'),
    ('verified', 'Vérifié'),
    ('rejected', 'Rejeté'),
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
    username = models.CharField("Nom d'utilisateur", max_length=100, unique=False, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True, verbose_name=_("Email"))
    country_code = models.CharField(max_length=4, choices=COUNTRY_CHOICES, default='+225', verbose_name="Indicatif pays")
    phone = models.CharField(max_length=15, unique=True)
    phone_full = models.CharField(max_length=25, unique=True)
    password = models.CharField(max_length=128)
    location = models.CharField(max_length=100, null=True, blank=True,choices=REGION_CHOICES,verbose_name="Région")
    stripe_account_id = models.CharField(max_length=255, null=True, blank=True)
    bio = models.CharField(max_length=100, blank=True, null=True)
    is_seller = models.BooleanField("Vendeur", default=False)
    is_seller_pending = models.BooleanField(default=False)
    is_active = models.BooleanField("En ligne", default=False)
    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField("Membre admin", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    auth_provider=models.CharField(max_length=50,default=AUTH_PROVIDERS.get("email"))
    objects = UserManager()
    full_name = models.CharField(max_length=150, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username', 'phone']

    def __str__(self):
        return f"{self.username or self.email}"
    @property
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    
    def save(self, *args, **kwargs):
        # 🔥 CORRECTION: Synchronisation automatique rôle ↔ statut vendeur
        if self.role == 'seller':
            self.is_seller = True
            # Si le profil vendeur est complété, approuver automatiquement
            if hasattr(self, 'vendor_profile') and self.vendor_profile.is_completed:
                self.is_seller_pending = False
        elif self.role == 'admin':
            self.is_seller = False
            self.is_seller_pending = False
        else:  # buyer
            self.is_seller = False
            self.is_seller_pending = False
            
        super().save(*args, **kwargs)
    def can_create_listing(self):
        """Vérifie si l'utilisateur peut créer une annonce"""
        return self.role == 'seller' and self.is_seller and not self.is_seller_pending
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
        return f"{self.user.get_full_name} - code"

# models.py - Ajoutez cette classe
# Dans models.py - Ajoutez cette classe après le modèle User

class VendorProfile(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ('individual', 'Individuel'),
        ('company', 'Entreprise'),
    ]
    
    VENDOR_TYPE_CHOICES = [
        ('retailer', 'Détaillant'),
        ('wholesaler', 'Grossiste'),
        ('manufacturer', 'Fabricant'),
        ('distributor', 'Distributeur'),
        ('individual', 'Particulier'),
    ]
    
    SHIPPING_ZONE_CHOICES = [
        ('Bamako', 'Bamako'),
        ('Ségou', 'Ségou'),
        ('Koulikoro', 'Koulikoro'),
    ]
    
    ID_TYPE_CHOICES = [
        ('carte-identite', 'Carte d\'identité'),
        ('passeport', 'Passeport'),
        ('permis-conduire', 'Permis de conduire'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor_profile')
    
    # === INFORMATIONS BOUTIQUE ===
    shop_name = models.CharField(max_length=255, blank=True, null=True)
    
    # Détails des communications
    contact_name = models.CharField(max_length=255, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Coordonnées du service client
    customer_service_name = models.CharField(max_length=255, blank=True, null=True)
    customer_service_phone = models.CharField(max_length=20, blank=True, null=True)
    customer_service_email = models.EmailField(blank=True, null=True)
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    
    # === INFORMATIONS SOCIÉTÉ ===
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, default='individual')
    company_name = models.CharField(max_length=255, blank=True, null=True)
    legal_representative = models.CharField(max_length=255, blank=True, null=True)
    id_type = models.CharField(max_length=20, choices=ID_TYPE_CHOICES, blank=True, null=True)
    tax_id = models.CharField(max_length=100, blank=True, null=True)
    vat_number = models.CharField(max_length=100, blank=True, null=True)
    legal_address = models.TextField(blank=True, null=True)
    
    # === INFORMATIONS EXPÉDITION ===
    shipping_zone = models.CharField(max_length=50, choices=SHIPPING_ZONE_CHOICES, default='Bamako')
    use_business_address = models.BooleanField(default=False)
    shipping_address_line1 = models.CharField(max_length=255, blank=True, null=True)
    shipping_address_line2 = models.CharField(max_length=255, blank=True, null=True)
    shipping_city = models.CharField(max_length=100, blank=True, null=True)
    shipping_state = models.CharField(max_length=100, blank=True, null=True)
    shipping_zip = models.CharField(max_length=20, blank=True, null=True)
    return_address_line1 = models.CharField(max_length=255, blank=True, null=True)
    return_address_line2 = models.CharField(max_length=255, blank=True, null=True)
    return_city = models.CharField(max_length=100, blank=True, null=True)
    return_state = models.CharField(max_length=100, blank=True, null=True)
    return_zip = models.CharField(max_length=20, blank=True, null=True)
    
    # === INFORMATIONS COMPLÉMENTAIRES ===
    has_existing_shop = models.CharField(max_length=3, choices=[('yes', 'Oui'), ('no', 'Non')], blank=True, null=True)
    vendor_type = models.CharField(max_length=20, choices=VENDOR_TYPE_CHOICES, blank=True, null=True)
    business_license = models.CharField(max_length=255, blank=True, null=True)
    
    # 🔥 AJOUT: Status fields that are missing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='pending')
    # === MÉTADONNÉES ===
    is_completed = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profil vendeur - {self.user.email}"

    def save(self, *args, **kwargs):
        # Vérifier si le profil est complété
        required_fields = ['shop_name', 'contact_name', 'contact_email', 'contact_phone']
        self.is_completed = all(getattr(self, field) for field in required_fields)
        if self.pk:  # Si l'instance existe déjà
            try:
                old_instance = VendorProfile.objects.get(pk=self.pk)
                if old_instance.status != 'approved' and self.status == 'approved':
                    self.verified_at = timezone.now()
                    self.verification_status = 'verified'
            except VendorProfile.DoesNotExist:
                pass  # Nouvelle instance
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Profil Vendeur"
        verbose_name_plural = "Profils Vendeurs"
# models.py - Ajoutez cette classe après le modèle VendorProfile

class Address(models.Model):
    ADDRESS_TYPE_CHOICES = [
        ('home', 'Maison'),
        ('work', 'Bureau'),
        ('billing', 'Adresse de facturation'),
        ('shipping', 'Adresse de livraison'),
        ('other', 'Autre'),
    ]
    
    REGION_CHOICES = [
        ('Bamako', 'Bamako'),
        ('Kayes', 'Kayes'),
        ('Koulikoro', 'Koulikoro'),
        ('Sikasso', 'Sikasso'),
        ('Ségou', 'Ségou'),
        ('Mopti', 'Mopti'),
        ('Tombouctou', 'Tombouctou'),
        ('Gao', 'Gao'),
        ('Kidal', 'Kidal'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    
    # Informations de base
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPE_CHOICES, default='home')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    
    # Coordonnées
    phone = models.CharField(max_length=20)
    additional_phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Adresse
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    region = models.CharField(max_length=50, choices=REGION_CHOICES, default='Bamako')
    delivery_point = models.CharField(max_length=255, blank=True, null=True)
    
    # Informations supplémentaires
    tax_id = models.CharField(max_length=100, blank=True, null=True)
    additional_info = models.TextField(blank=True, null=True)
    
    # Options
    is_default = models.BooleanField(default=False)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Adresse"
        verbose_name_plural = "Adresses"
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.address_line1}, {self.city}"

    def save(self, *args, **kwargs):
        # Si cette adresse est définie comme défaut, désactiver les autres adresses par défaut
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    @property
    def full_address(self):
        lines = [self.address_line1]
        if self.address_line2:
            lines.append(self.address_line2)
        lines.extend([self.city, self.region])
        return ', '.join(filter(None, lines))
        