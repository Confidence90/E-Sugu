# e_sugu/views.py
from rest_framework.response import Response
from rest_framework.views import APIView

class HomeView(APIView):
    def get(self, request):
        return Response({
            "message": "Bienvenue sur l'API E-Sugu !",
            "status": "API is running",
            "endpoints": {
                "users": "/api/users/",
                "listings": "/api/listings/",
                "categories": "/api/categories/",
                "favorites": "/api/favorites/",
                "payments": "/api/payments/",
                "discussion": "/api/discussion/",
                "notifications": "/api/notifications/",
                "reviews": "/api/reviews/",
                "events": "/api/events/",
                "administration": "/api/administration/",
            }
        })