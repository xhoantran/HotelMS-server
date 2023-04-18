import datetime
import uuid

from django.db.models import Q

from backend.utils.channex_client import ChannexClient

from ..models import RatePlan, RatePlanRestrictions, RoomType
from ..serializers import RatePlanRestrictionsSerializer
from .base import PMSBaseAdapter


class ChannexPMSAdapter(PMSBaseAdapter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = ChannexClient(api_key=self.hotel.external_api_key)

    @staticmethod
    def _date_format(date: datetime.date | str) -> str:
        if isinstance(date, str):
            return date
        return date.strftime("%Y-%m-%d")

    @staticmethod
    def validate_api_key(api_key: str):
        client = ChannexClient(api_key=api_key)
        response = client.get_properties()
        return response.status_code == 200

    @staticmethod
    def validate_external_id(external_id: str):
        client = ChannexClient(api_key=external_id)
        response = client.get_property(external_id)
        return response.status_code == 200

    def get_room_type_rate_plan_restrictions(
        self,
        room_type: RoomType | uuid.UUID | str = None,
        date: datetime.date | str = None,
        date_from: datetime.date | str = None,
        date_to: datetime.date | str = None,
        *args,
        **kwargs,
    ):
        # Prepare params
        params = {"property_id": self.hotel.external_id}
        if room_type:
            params["room_type_id"] = self._convert_to_id(
                room_type,
                RoomType,
                field_name="external_id",
            )
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
        for rate_plan_external_id, _ in data.items():
            rate_plans.append(
                RatePlan(
                    room_type__hotel=self.hotel,
                    external_id=rate_plan_external_id,
                    room_type_id=params["room_type_id"],
                )
            )
        rate_plans = RatePlan.objects.bulk_create(rate_plans, ignore_conflicts=True)

        # Get rate plan restrictions
        rate_plan_restriction_objects = RatePlanRestrictions.objects.filter(
            rate_plan__in=rate_plans,
            date__gte=date_from,
            date__lte=date_to,
        )
        for rate_plan_restriction in rate_plan_restriction_objects:
            rate_plan_external_id = rate_plan_restriction.rate_plan.external_id
            date = rate_plan_restriction.date
            rate_plan_restriction(
                **data[rate_plan_external_id][self._date_format(date)]
            )

        # Get updated fields
        updated_fields = next(iter(data.values()))[self._date_format(date_from)].keys()

        # Validate data
        return RatePlanRestrictions.objects.bulk_update(
            rate_plan_restriction_objects,
            updated_fields=updated_fields,
        )
