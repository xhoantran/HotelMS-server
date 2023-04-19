from backend.utils.channex_client import ChannexClient

from ..models import RatePlan, RoomType
from .base import PMSBaseAdapter


class ChannexPMSAdapter(PMSBaseAdapter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = ChannexClient(api_key=self.hotel.pms_api_key)

    @staticmethod
    def validate_api_key(api_key: str):
        client = ChannexClient(api_key=api_key)
        response = client.get_properties()
        return response.status_code == 200

    @staticmethod
    def validate_pms_id(pms_id: str):
        client = ChannexClient(api_key=pms_id)
        response = client.get_property(pms_id)
        return response.status_code == 200

    def sync_up(self):
        # Get properties
        response = self.client.get_property(self.hotel.pms_id)
        if response.status_code != 200:
            raise Exception(response.json())
        data = response.json().get("data")
        self.hotel.inventory_days = data["attributes"]["settings"]["state_length"]
        self.hotel.save(update_fields=["inventory_days"])

        # Get room types and rate plans
        response = self.client.get_rate_plans(property_id=self.hotel.pms_id)
        if response.status_code != 200:
            raise Exception(response.json())
        data = response.json().get("data")
        room_type_pms_ids = set()
        room_type_objects = []

        # Create room types
        for rate_plan in data:
            if rate_plan["attributes"]["room_type_id"] not in room_type_pms_ids:
                room_type_objects.append(
                    RoomType(
                        pms_id=rate_plan["attributes"]["room_type_id"],
                        hotel=self.hotel,
                    )
                )
                room_type_pms_ids.add(rate_plan["attributes"]["room_type_id"])
        room_types = RoomType.objects.bulk_create(
            room_type_objects, ignore_conflicts=True
        )

        # If hotel has room types, start creating rate plans
        if len(room_types) > 0:
            # If bulk_create not return id
            if room_types[0].id is None:
                room_types = RoomType.objects.filter(
                    pms_id__in=room_type_pms_ids, hotel=self.hotel
                )

            # Create room type id map
            room_type_id_map = {
                str(room_type.pms_id): room_type.id for room_type in room_types
            }

            # Create rate plans
            rate_plan_objects = []
            for rate_plan in data:
                rate_plan_objects.append(
                    RatePlan(
                        pms_id=rate_plan["id"],
                        # using room_type_id_map to get the id of the room type
                        room_type_id=room_type_id_map[
                            rate_plan["attributes"]["room_type_id"]
                        ],
                    )
                )
            RatePlan.objects.bulk_create(rate_plan_objects, ignore_conflicts=True)
