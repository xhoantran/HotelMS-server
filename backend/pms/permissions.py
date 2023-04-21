from rest_framework_api_key.permissions import BaseHasAPIKey

from .models import HotelAPIKey


class HasHotelAPIKey(BaseHasAPIKey):
    model = HotelAPIKey
