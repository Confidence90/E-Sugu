# tests/test_listings_api.py

import pytest
from rest_framework.test import APIClient
from listings.models import Listing, Category
from users.models import User

@pytest.mark.django_db
def test():
    user = User.objects.create_user(
        email="testuser@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
        phone="1234567890"
    )

    category = Category.objects.create(name="Immobilier")

    listing = Listing.objects.create(
        user=user,
        title="Maison en vedette",
        category=category,  # ← ici on passe un objet Category, pas une string
        subcategory="villa",
        price=150000,
        description="Une superbe villa avec piscine.",
        is_featured=True,
        is_published=True
    )

    assert listing.title == "Maison en vedette"
    assert listing.is_featured is True


@pytest.mark.django_db
def test_get_featured_listings():
    client = APIClient()

    user = User.objects.create_user(
        email="testuser@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
        phone="1234567890"
    )

    category = Category.objects.create(name="Immobilier")

    listing = Listing.objects.create(
        user=user,
        title="Villa Featured",
        category=category,  # ← idem ici
        subcategory="villa",
        price=250000,
        description="Villa avec vue sur mer",
        is_featured=True,
        is_published=True
    )

    response = client.get("/api/listings/featured/?subcategory=villa")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(item["id"] == listing.id for item in data)
