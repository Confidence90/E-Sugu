# notifications/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Notification
from .serializers import NotificationSerializer
from rest_framework.permissions import AllowAny
class NotificationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(user=request.user)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class NotificationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, id):
        try:
            notification = Notification.objects.get(id=id, user=request.user)
            notification.is_read = True
            notification.save()
            serializer = NotificationSerializer(notification)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response({'error': 'Notification non trouvée'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, id):
        try:
            notification = Notification.objects.get(id=id, user=request.user)
            notification.delete()
            return Response({'message': 'Notification supprimée'}, status=status.HTTP_204_NO_CONTENT)
        except Notification.DoesNotExist:
            return Response({'error': 'Notification non trouvée'}, status=status.HTTP_404_NOT_FOUND)

