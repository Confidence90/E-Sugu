from django.contrib import admin
from django.utils.html import format_html
from django.conf import settings
from .models import User
from twilio.rest import Client

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'nom', 'email', 'telephone', 'actif', 'staff',
        'date_creation', 'token_display'
    ]
    search_fields = ['name', 'email', 'phone_full']
    list_filter = ['is_active', 'is_staff', 'created_at']
    actions = [
        'desactiver_utilisateurs',
        'reinitialiser_mot_de_passe',
        'demander_reinitialisation'
    ]

    def nom(self, obj):
        return obj.name
    nom.short_description = "Nom"

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
