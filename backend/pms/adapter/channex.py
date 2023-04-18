import datetime
import uuid

from backend.utils.channex_client import ChannexClient

from ..models import RatePlan, RatePlanRestrictions, RoomType
from ..serializers import RatePlanRestrictionsSerializer
from .base import PMSBaseAdapter


class ChannexPMSAdapter(PMSBaseAdapter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = ChannexClient(api_key=self.hotel.pms_api_key)

    @staticmethod
    def _normalize_date_format(date: datetime.date | str) -> str:
        if isinstance(date, str):
            return date
        return date.strftime("%Y-%m-%d")

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

    def set_up(self):
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

    def get_room_type_rate_plan_restrictions(
        self,
        room_type: RoomType | uuid.UUID | str,
        date: datetime.date | str = None,
        date_from: datetime.date | str = None,
        date_to: datetime.date | str = None,
        restrictions: list[str] = ["rate"],
        *args,
        **kwargs,
    ):
        # Prepare params
        params = {"property_id": self.hotel.pms_id}
        params["room_type_id"] = self._convert_to_id(
            room_type,
            RoomType,
            field_name="pms_id",
        )
        params["restrictions"] = restrictions
        try:
            room_type = RoomType.objects.get(
                pms_id=params["room_type_id"],
                hotel=self.hotel,
            )
        except RoomType.DoesNotExist:
            raise ValueError("Room type does not belong to this hotel")

        if date:
            params["date"] = date
            date_from = date
            date_to = date
        elif date_from and date_to:
            params["date_from"] = date_from
            params["date_to"] = date_to
        else:
            raise ValueError("Date or date range must be provided")

        # Get data
        response = self.client.get_room_type_rate_plan_restrictions(**params)
        if response.status_code != 200:
            raise Exception(response.json())

        # Parse response
        data = response.json().get("data")

        # Get rate plans
        rate_plans = []
        for rate_plan_pms_id, _ in data.items():
            rate_plans.append(
                RatePlan(
                    pms_id=rate_plan_pms_id,
                    room_type=room_type,
                )
            )
        RatePlan.objects.bulk_create(rate_plans, ignore_conflicts=True)

        # Get rate plan restrictions
        rate_plan_restriction_objects = RatePlanRestrictions.objects.filter(
            rate_plan__room_type=room_type,
            date__gte=date_from,
            date__lte=date_to,
        )
        for rate_plan_restriction in rate_plan_restriction_objects:
            rate_plan_pms_id = rate_plan_restriction.rate_plan.pms_id
            date = rate_plan_restriction.date
            rate_plan_restriction(
                **data[rate_plan_pms_id][self._normalize_date_format(date)]
            )

        # Validate data
        RatePlanRestrictions.objects.bulk_update(
            rate_plan_restriction_objects, restrictions
        )
        return RatePlanRestrictionsSerializer(
            rate_plan_restriction_objects,
            many=True,
        ).data
