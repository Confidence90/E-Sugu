from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DiscussionViewSet, SendMessageView

router = DefaultRouter()
router.register('discussions', DiscussionViewSet, basename='discussion')

urlpatterns = router.urls + [
    path('send-message/', SendMessageView.as_view(), name='send_message'),
]
