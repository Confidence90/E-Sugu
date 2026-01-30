# reviews/urls.py
from django.urls import path
from .views import *
urlpatterns = [
    path('', ReviewView.as_view(), name='reviews-list-create'),
    path('<int:id>/', ReviewDetailView.as_view(), name='review-detail'),
    path('user/<int:user_id>/', UserReviewsView.as_view(), name='user-reviews'),
    path('platform/', PlatformReviewsView.as_view(), name='platform-reviews'),
    path('<int:review_id>/reply/', ReplyToReviewView.as_view(), name='reply-to-review'),
    path('<int:review_id>/vote/', VoteOnReviewView.as_view(), name='vote-on-review'),
    path('listing/<int:listing_id>/', ListingReviewView.as_view(), name='listing-review'),
]