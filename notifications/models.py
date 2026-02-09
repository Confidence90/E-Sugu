from django.db import models
from users.models import User


class Notification(models.Model):
    TYPE_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Avertissement'),
        ('success', 'Succès'),
        ('error', 'Erreur'),
        ('promotion', 'Promotion'),
        ('system', 'Système'),
        ('order', 'Commande'),
        ('payment', 'Paiement'),
        ('user', 'Utilisateur'),
        ('support', 'Support'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Basse'),
        ('medium', 'Moyenne'),
        ('high', 'Haute'),
        ('urgent', 'Urgente'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    admin_only = models.BooleanField(default=False) 
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='system')
    data = models.JSONField(default=dict, blank=True)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    is_handled = models.BooleanField(default=False)  # Traitée par l'admin
    handled_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='handled_notifications'
    )
    handled_at = models.DateTimeField(null=True, blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_notifications'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']  # Par défaut, les plus récentes d'abord
        indexes = [
            models.Index(fields=['admin_only', 'is_handled']),
            models.Index(fields=['priority']),
            models.Index(fields=['type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f"[{self.get_type_display()}] {self.content[:50]}"
    
    def save(self, *args, **kwargs):
        # Définir automatiquement la date d'expiration (30 jours par défaut)
        from django.utils.timezone import now, timedelta
        if not self.expires_at:
            self.expires_at = now() + timedelta(days=30)
        
        # Si c'est une notification admin_only, on ne l'assigne pas à un utilisateur spécifique
        if self.admin_only and self.user:
            self.user = None
            
        super().save(*args, **kwargs)
    
    def is_expired(self):
        from django.utils.timezone import now
        if self.expires_at:
            return now() > self.expires_at
        return False
    
    def mark_as_read(self):
        """Marquer la notification comme lue"""
        self.is_read = True
        self.save()
    
    def mark_as_handled(self, user):
        """Marquer la notification comme traitée"""
        from django.utils.timezone import now
        self.is_handled = True
        self.handled_by = user
        self.handled_at = now()
        self.save()