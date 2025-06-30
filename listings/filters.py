# listings/filters.py
import django_filters
from .models import Listing

class ListingFilter(django_filters.FilterSet):
    price_min = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_max = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    category = django_filters.CharFilter(field_name="category__name", lookup_expr="icontains")
    condition = django_filters.ChoiceFilter(field_name="condition", choices=[('new', 'Neuf'), ('used', 'Occasion')])
    location = django_filters.CharFilter(field_name="location", lookup_expr="icontains")
    status = django_filters.ChoiceFilter(field_name="status", choices=[('active', 'Actif'), ('sold', 'Vendu'), ('expired', 'Expiré')])
    type = django_filters.ChoiceFilter(field_name="type", choices=[('sale', 'Vente'), ('rental', 'Location')])

    class Meta:
        model = Listing
        fields = ['category', 'price_min', 'price_max', 'condition', 'location', 'status', 'type']
