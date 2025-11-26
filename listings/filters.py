# listings/filters.py
import django_filters
from .models import Listing
from categories.models import Category

class ListingFilter(django_filters.FilterSet):
    price_min = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_max = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    category = django_filters.CharFilter(method='filter_category')
    condition = django_filters.ChoiceFilter(field_name="condition", choices=[('new', 'Neuf'), ('used', 'Occasion')])
    location = django_filters.CharFilter(field_name="location", lookup_expr="icontains")
    status = django_filters.ChoiceFilter(field_name="status", choices=[('active', 'Actif'), ('sold', 'Vendu'), ('expired', 'Expiré')])
    type = django_filters.ChoiceFilter(field_name="type", choices=[('sale', 'Vente'), ('rental', 'Location')])
    is_featured = django_filters.BooleanFilter(field_name="is_featured")

    class Meta:
        model = Listing
        fields = ['category', 'price_min', 'price_max', 'condition', 'location', 'status', 'type', 'is_featured']
    
    def filter_category(self, queryset, name, value):
        """
        Filtre les annonces dont la catégorie est `value` ou une sous-catégorie de `value`.
        """
        try:
            # Récupérer la catégorie principale par nom (insensible à la casse)
            category = Category.objects.get(name__iexact=value)
        except Category.DoesNotExist:
            return queryset.none()

        # Récupérer les sous-catégories de cette catégorie
        subcategories = Category.objects.filter(parent=category)

        # Liste des ids à filtrer : catégorie + sous-catégories
        category_ids = [category.id] + list(subcategories.values_list('id', flat=True))

        # Filtrer les annonces avec category dans cette liste
        return queryset.filter(category_id__in=category_ids)