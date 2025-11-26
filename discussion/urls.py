# discussion/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register('discussions', DiscussionViewSet, basename='discussion')

urlpatterns = router.urls + [
    path('send-message/', SendMessageView.as_view(), name='send_message'),
    path('admin/discussions/', AdminDiscussionView.as_view(), name='admin_discussions'),
]
