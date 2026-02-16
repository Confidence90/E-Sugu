#admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.conf import settings
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.admin import SimpleListFilter
from .models import User
from twilio.rest import Client
from datetime import timedelta
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .forms import UserCreationForm, UserChangeForm
import random
from django.core.mail import EmailMessage
from django.contrib import messages
from .models import *


# 📊 Filtre personnalisé : activité récente
class RecentLoginFilter(SimpleListFilter):
    title = "Connexion récente"
    parameter_name = "recent_login"

    def lookups(self, request, model_admin):
        return [
            ('24h', "Dernières 24h"),
            ('7d', "7 derniers jours"),
        ]

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == '24h':
            return queryset.filter(last_login__gte=now - timedelta(hours=24))
        elif self.value() == '7d':
            return queryset.filter(last_login__gte=now - timedelta(days=7))
        return queryset

class RoleFilter(SimpleListFilter):
    title = 'Rôle'
    parameter_name = 'role'

    def lookups(self, request, model_admin):
        return User.ROLE_CHOICES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(role=self.value())
        return queryset


# 📞 Filtre personnalisé : type de numéro
class PhoneTypeFilter(SimpleListFilter):
    title = 'Type de téléphone'
    parameter_name = 'phone_type'

    def lookups(self, request, model_admin):
        return [('intl', '📞 International'), ('local', '📱 National')]

    def queryset(self, request, queryset):
        if self.value() == 'intl':
            return queryset.filter(phone_full__startswith='+')
        elif self.value() == 'local':
            return queryset.exclude(phone_full__startswith='+')
        return queryset

# 🔧 Admin personnalisé

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ('email',)
    list_display = ['id','email', 'first_name', 'last_name', 'phone', 'is_staff', 'is_superuser']
    search_fields = ['email', 'first_name', 'last_name', 'phone']
    list_filter = ['is_active', 'is_staff', 'is_superuser',PhoneTypeFilter,RoleFilter]
    readonly_fields = ['created_at']
    add_form = UserCreationForm
    form = UserChangeForm


    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Informations personnelles'), {
            'fields': ('first_name', 'last_name', 'username', 'phone', 'phone_full', 'country_code', 'location', 'bio')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        (_('Dates importantes'), {'fields': ('last_login', 'created_at')}),
        (_('Rôle'), {'fields': ('role',)}),
    )

    add_fieldsets = (
    (None, {
        'classes': ('wide',),
        'fields': (
            'email', 'first_name', 'last_name', 'username', 'phone',
            'phone_full', 'password1', 'password2',
            'is_staff', 'is_superuser', 'is_active'  # ✅ à ajouter
        ),
    }),
    )
    actions = [ 'desactiver_utilisateurs', 'reinitialiser_mot_de_passe', 'demander_reinitialisation' ]
    


    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        if not obj:
            self.fieldsets = self.add_fieldsets
        return super().get_form(request, obj, **kwargs)

    def telephone(self, obj):
        return obj.phone_full
    telephone.short_description = "Téléphone"

    def actif(self, obj):
        return obj.is_active
    actif.short_description = "Actif"

    def staff(self, obj):
        return obj.is_staff
    staff.short_description = "Admin"

    def date_creation(self, obj):
        return obj.created_at
    date_creation.short_description = "Créé le"

    def token_display(self, obj):
        if obj.is_active:
            token = obj.get_token()
            return format_html(
                f'<input type="text" value="{token}" readonly id="token_{obj.id}" style="width:300px;" />'
                f'<button onclick="navigator.clipboard.writeText(document.getElementById(\'token_{obj.id}\').value)">Copier</button>'
            )
        return "—"
    token_display.short_description = "Token JWT"

    def desactiver_utilisateurs(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} utilisateur(s) désactivé(s).")
    desactiver_utilisateurs.short_description = "🚫 Désactiver les utilisateurs sélectionnés"

    def reinitialiser_mot_de_passe(self, request, queryset):
        for user in queryset:
            user.set_password('demo1234')
            user.save()
        self.message_user(request, f"{queryset.count()} utilisateur(s) réinitialisé(s) avec le mot de passe 'demo1234'.")
    reinitialiser_mot_de_passe.short_description = "🔁 Réinitialiser mot de passe (demo1234)"

    def demander_reinitialisation(self, request, queryset):
        """Envoyer un code de réinitialisation par email aux utilisateurs sélectionnés"""
        success_count = 0
        errors = []
        
        for user in queryset:
            try:
                # Vérifier si l'utilisateur a un email
                if not user.email:
                    errors.append(f"Pas d'email pour l'utilisateur {user.username}")
                    continue
                
                # Générer un code OTP
                code = ''.join(str(random.randint(0, 9)) for _ in range(6))
                
                # Supprimer les anciens OTP de l'utilisateur
                OneTimePassword.objects.filter(user=user).delete()
                
                # Créer un nouveau OTP
                OneTimePassword.objects.create(
                    user=user,
                    code=code
                )
                
                # Préparer l'email
                subject = "🔐 Réinitialisation de votre mot de passe E-Sugu"
                from_email = settings.DEFAULT_FROM_EMAIL
                site_name = "E-sugu"
                
                message = f"""
Bonjour {user.first_name or user.username},

Vous avez demandé la réinitialisation de votre mot de passe E-Sugu.

Voici votre code de réinitialisation : **{code}**

⏰ Ce code est valable pendant 5 minutes.

🔒 **Sécurité importante :**
- Ne partagez jamais ce code
- Si vous n'avez pas fait cette demande, ignorez cet email
- Contactez notre support en cas de doute

Pour réinitialiser votre mot de passe :
1. Rendez-vous sur la page de réinitialisation
2. Entrez votre email et ce code
3. Créez votre nouveau mot de passe

Merci de nous aider à garder votre compte sécurisé.

Cordialement,
L'équipe {site_name}
                """
                
                # Envoyer l'email
                email = EmailMessage(subject, message, from_email, [user.email])
                email.send(fail_silently=False)
                
                success_count += 1
                
            except Exception as e:
                errors.append(f"Erreur pour {user.email}: {str(e)}")
        
        # Message de succès
        if success_count > 0:
            self.message_user(
                request, 
                f"{success_count} email(s) de réinitialisation envoyé(s) avec succès.",
                level=messages.SUCCESS
            )
        
        # Afficher les erreurs s'il y en a
        if errors:
            error_message = "Erreurs survenues :<br>" + "<br>".join(errors[:5])  # Limiter à 5 erreurs
            if len(errors) > 5:
                error_message += f"<br>... et {len(errors) - 5} erreur(s) supplémentaires"
            self.message_user(
                request, 
                error_message,
                level=messages.ERROR
            )
    
    demander_reinitialisation.short_description = "📧 Envoyer email de réinitialisation"

@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'shop_name', 'verification_status', 'kyc_confidence_score', 'kyc_submitted_at', 'actions']
    list_filter = ['verification_status', 'account_type', 'status']
    search_fields = ['shop_name', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['kyc_submitted_at', 'kyc_reviewed_at']
    
    fieldsets = (
        ('Informations boutique', {
            'fields': ('shop_name', 'user')
        }),
        ('Documents KYC', {
            'fields': ('id_front_image', 'id_back_image', 'proof_of_address', 'business_registration')
        }),
        ('Statut', {
            'fields': ('verification_status', 'kyc_confidence_score', 'kyc_rejection_reason')
        }),
        ('Dates', {
            'fields': ('kyc_submitted_at', 'kyc_reviewed_at', 'kyc_reviewed_by')
        }),
    )
    
    def admin_actions(self, obj):
        """Afficher les boutons d'action pour l'admin"""
        if obj.verification_status == 'pending':
            return format_html(
                '<div class="admin-actions">'
                '<a class="button approve-button" href="/api/users/admin/kyc/{}/approve/" '
                'onclick="return confirm(\'Êtes-vous sûr de vouloir approuver ce KYC ?\')">'
                '✓ Approuver KYC</a>&nbsp;'
                '<a class="button reject-button" href="/api/users/admin/kyc/{}/reject/" '
                'onclick="return confirm(\'Êtes-vous sûr de vouloir rejeter ce KYC ?\')">'
                '✗ Rejeter KYC</a>'
                '</div>',
                obj.user_id, obj.user_id
            )
        return format_html(
            '<span class="status-badge {}">{}</span>',
            obj.verification_status,
            obj.get_verification_status_display()
        )
    admin_actions.short_description = 'Actions Admin'
    admin_actions.allow_tags = True
    
    class Media:
        css = {
            'all': (
                'css/admin-custom.css',
            )
        }