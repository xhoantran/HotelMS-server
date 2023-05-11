from rest_framework.test import APIRequestFactory

from ..models import HotelAPIKey
from ..permissions import HasCMHotelAPIKey


def test_has_cm_hotel_api_key_permission(cm_hotel_factory, mocked_channex_validation):
    permission = HasCMHotelAPIKey()

    request = APIRequestFactory().get("/", HTTP_AUTHORIZATION="Api-Key 123")
    assert not permission.has_permission(request, None)

    cm_hotel = cm_hotel_factory(channex=True)
    _, api_key = HotelAPIKey.objects.create_key(hotel=cm_hotel, name="API Key")
    request = APIRequestFactory().get("/", HTTP_AUTHORIZATION=f"Api-Key {api_key}")
    assert permission.has_permission(request, None)
