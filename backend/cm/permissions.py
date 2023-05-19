from rest_framework_api_key.permissions import BaseHasAPIKey

from .models import CMHotelConnectorAPIKey


class HasCMHotelConnectorAPIKey(BaseHasAPIKey):
    model = CMHotelConnectorAPIKey
