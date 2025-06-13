# reviews/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Review
from .serializers import ReviewSerializer, CreateReviewSerializer

class ReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(reviewer=request.user)
            return Response(ReviewSerializer(serializer.instance).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        reviews = Review.objects.filter(reviewed=request.user)
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ReviewDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            review = Review.objects.get(id=id)
            serializer = ReviewSerializer(review)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Review.DoesNotExist:
            return Response({'error': 'Avis non trouvé'}, status=status.HTTP_404_NOT_FOUND)