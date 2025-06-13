# messages/urls.py
from django.urls import path
from .views import MessageView, MessageDetailView

urlpatterns = [
    path('', MessageView.as_view(), name='discussion'),
    path('<int:id>/', MessageDetailView.as_view(), name='message-detail'),
]