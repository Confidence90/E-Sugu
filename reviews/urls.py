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

    path('seller/', SellerReviewsView.as_view(), name='seller-reviews'),
    path('seller/listing/<int:listing_id>/', SellerListingReviewsView.as_view(), name='seller-listing-reviews'),

    path('seller/average-rating/', SellerAverageRatingView.as_view(), name='seller-average-rating'),
    path('seller/positive-reviews/', SellerPositiveReviewsView.as_view(), name='seller-positive-reviews'),
    path('seller/pending-reply/', SellerPendingReplyView.as_view(), name='seller-pending-reply'),
    path('seller/response-history/', SellerResponseHistoryView.as_view(), name='seller-response-history'),
    path('seller/analytics/', SellerReviewAnalyticsView.as_view(), name='seller-analytics'),    
]