from django.db import models
from users.models import User

class Discussion(models.Model):
    # ❌ SUPPRIMEZ le champ listing - les discussions sont indépendantes
    title = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        verbose_name="Sujet de la discussion"
    )
    participant1 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conversations_as_participant1'
    )
    participant2 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conversations_as_participant2'
    )
    discussion_type = models.CharField(
        max_length=20,
        choices=[
            ('buyer_admin', 'Acheteur ↔ Admin'),
            ('seller_admin', 'Vendeur ↔ Admin'),
            ('support', 'Support général'),
        ],
        default='support'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('participant1', 'participant2')  # ❌ Supprimez listing de unique_together
        ordering = ['-updated_at']

    def __str__(self):
        title_display = f" - {self.title}" if self.title else ""
        return f"Discussion {self.id}{title_display} : {self.participant1} ↔ {self.participant2}"

    def is_admin_involved(self):
        """Vérifier si un admin participe à la discussion"""
        return (self.participant1.is_staff or self.participant1.is_superuser or 
                self.participant2.is_staff or self.participant2.is_superuser)

    def get_other_participant(self, user):
        """Récupérer l'autre participant"""
        if user == self.participant1:
            return self.participant2
        return self.participant1

    def mark_as_read_for_user(self, user):
        """Marquer tous les messages comme lus pour un utilisateur"""
        self.messages.filter(is_read=False).exclude(sender=user).update(is_read=True)

class Message(models.Model):
    discussion = models.ForeignKey(
        Discussion,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username} → Discussion {self.discussion.id}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Mettre à jour la date de modification de la discussion
        self.discussion.updated_at = self.created_at
        self.discussion.save(update_fields=['updated_at'])