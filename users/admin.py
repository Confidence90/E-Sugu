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
    list_display = ['id', 'email', 'username', 'is_active', 'is_staff']
    search_fields = ['email', 'username', 'phone']
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
        for user in queryset:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.verify.services(settings.TWILIO_VERIFY_SERVICE_SID).verifications.create(
                to=user.phone_full,
                channel='sms'
            )
        self.message_user(request, f"{queryset.count()} utilisateur(s) ont reçu un code de réinitialisation.")
    demander_reinitialisation.short_description = "🔐 Envoyer code pour réinitialiser le mot de passe"
