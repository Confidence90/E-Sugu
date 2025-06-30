from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Discussion, Message
from listings.models import Listing
from .serializers import DiscussionSerializer, MessageSerializer, CreateMessageSerializer
from users.models import User
from django.db import models

from rest_framework.decorators import action

class DiscussionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DiscussionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Discussion.objects.filter(models.Q(buyer=user) | models.Q(seller=user))

class SendMessageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CreateMessageSerializer(data=request.data)
        if serializer.is_valid():
            listing_id = serializer.validated_data['listing_id']
            content = serializer.validated_data['content']
            try:
                listing = Listing.objects.get(id=listing_id)
                seller = listing.user
                buyer = request.user

                if seller == buyer:
                    return Response({'error': "Tu ne peux pas t'envoyer un message."}, status=400)

                discussion, created = Discussion.objects.get_or_create(
                    listing=listing, buyer=buyer, seller=seller
                )

                message = Message.objects.create(
                    discussion=discussion,
                    sender=buyer,
                    content=content
                )

                return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)

            except Listing.DoesNotExist:
                return Response({'error': 'Annonce non trouvée.'}, status=404)
        return Response(serializer.errors, status=400)
