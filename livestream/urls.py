from django.urls import path
from .views import LiveStreamCreateView

urlpatterns = [
    path('create/', LiveStreamCreateView.as_view(), name='livestream_create'),
]