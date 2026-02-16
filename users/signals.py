# users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from users.models import User
from notifications.models import Notification


@receiver(post_save, sender=User)
def notify_admin_on_user_registration(sender, instance, created, **kwargs):
    if not created:
        return

    Notification.objects.create(
        admin_only=True,
        type='user',
        priority='medium',
        content=f"👤 Nouvel utilisateur inscrit : {instance.email} ({instance.role})",
        data={
            "user_id": instance.id,
            "email": instance.email,
            "role": instance.role,
            "is_active": instance.is_active,
            "is_seller_pending": instance.is_seller_pending,
        }
    )
