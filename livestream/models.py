from django.db import models
from users.models import User

class LiveStream(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='livestreams')
    title = models.CharField(max_length=200)
    stream_url = models.URLField()
    start_time = models.DateTimeField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)