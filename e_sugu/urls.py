# e_sugu/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Interface d'administration Django
    path('admin/', admin.site.urls),
    
    # Routes des modules (applications)
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
]

# Servir les fichiers médias en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)