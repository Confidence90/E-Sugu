from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import LiveStream
from .serializers import LiveStreamSerializer

class LiveStreamCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = {'user': request.user.id, 'title': request.data.get('title'), 'stream_url': request.data.get('stream_url'), 'start_time': request.data.get('start_time')}
        serializer = LiveStreamSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)