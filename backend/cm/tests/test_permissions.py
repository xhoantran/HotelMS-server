from rest_framework.test import APIRequestFactory

from ..models import CMHotelConnectorAPIKey
from ..permissions import HasCMHotelConnectorAPIKey


def test_has_cm_hotel_api_key_permission(
    mocked_channex_validation, cm_hotel_connector_factory
):
    permission = HasCMHotelConnectorAPIKey()

    request = APIRequestFactory().get("/", HTTP_AUTHORIZATION="Api-Key 123")
    assert not permission.has_permission(request, None)

    cm_hotel = cm_hotel_connector_factory(channex=True)
    _, api_key = CMHotelConnectorAPIKey.objects.create_key(
        name="API Key",
        cm_hotel_connector=cm_hotel,
    )
    request = APIRequestFactory().get("/", HTTP_AUTHORIZATION=f"Api-Key {api_key}")
    assert permission.has_permission(request, None)
