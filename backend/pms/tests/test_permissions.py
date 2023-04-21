from rest_framework.test import APIRequestFactory

from ..models import HotelAPIKey
from ..permissions import HasHotelAPIKey


def test_admin_permission(hotel_factory):
    permission = HasHotelAPIKey()

    request = APIRequestFactory().get("/", HTTP_AUTHORIZATION="Api-Key 123")
    assert not permission.has_permission(request, None)

    hotel = hotel_factory()
    _, api_key = HotelAPIKey.objects.create_key(hotel=hotel, name="API Key")
    request = APIRequestFactory().get("/", HTTP_AUTHORIZATION=f"Api-Key {api_key}")
    assert permission.has_permission(request, None)
