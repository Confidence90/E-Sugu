# e_sugu/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import HomeView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),  # Route pour l'URL racine
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/listings/', include('listings.urls')),
    path('api/categories/', include('categories.urls')),
    path('api/favorites/', include('favorites.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/discussion/', include('discussion.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/reviews/', include('reviews.urls')),
    path('api/events/', include('events.urls')),
    path('api/administration/', include('administration.urls')),
    path('api/paniers/', include('paniers.urls')),
    path('api/commandes/', include('commandes.urls')),
    path('api/livestream/', include('livestream.urls')),
    path('api/transactions/', include('transactions.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)