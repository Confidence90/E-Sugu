# messages/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Message
from .serializers import MessageSerializer, CreateMessageSerializer

class MessageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateMessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(sender=request.user)
            return Response(MessageSerializer(serializer.instance).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        listing_id = request.query_params.get('listing_id')
        messages = Message.objects.filter(sender=request.user) | Message.objects.filter(receiver=request.user)
        if listing_id:
            messages = messages.filter(listing_id=listing_id)
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class MessageDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            message = Message.objects.get(id=id)
            if message.sender == request.user or message.receiver == request.user:
                serializer = MessageSerializer(message)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response({'error': 'Non autorisé'}, status=status.HTTP_403_FORBIDDEN)
        except Message.DoesNotExist:
            return Response({'error': 'Message non trouvé'}, status=status.HTTP_404_NOT_FOUND)