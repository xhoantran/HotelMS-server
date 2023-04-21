from django.contrib.sites.models import Site
from django.db.models import Prefetch
from django.urls import reverse
from django.utils import timezone

from backend.rms.adapter import DynamicPricingAdapter
from backend.utils.channex_client import ChannexClient

from ..models import RatePlan, RatePlanRestrictions, RoomType
from .base import PMSBaseAdapter


class ChannexPMSAdapter(PMSBaseAdapter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = ChannexClient(api_key=self.hotel.pms_api_key)

    def load_rms_adapter(self):
        self.rms_adapter = DynamicPricingAdapter(self.hotel)

    @staticmethod
    def validate_api_key(api_key: str):
        client = ChannexClient(api_key=api_key)
        response = client.get_properties()
        return response.status_code == 200

    @staticmethod
    def validate_pms_id(api_key: str, pms_id: str):
        client = ChannexClient(api_key=api_key)
        response = client.get_property(pms_id)
        return response.status_code == 200

    def _set_up_room_type_webhook(
        self,
        room_type_uuid: str,
        room_type_pms_id: str,
        api_key: str,
        callback_url: str,
    ):
        response = self.client.create_webhook(
            property_id=str(self.hotel.pms_id),
            callback_url=callback_url,
            event_mask=f"ari:availability:{room_type_pms_id}:*",
            request_params={"room_type_uuid": room_type_uuid},
            headers={"Api-Key": api_key},
        )
        if response.status_code != 201:
            raise Exception(response.json())

    def sync_up(self, api_key: str):
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

            current_site = Site.objects.get_current()
            room_type_id_map = {}
            for room_type in room_types:
                # Create room type id map
                room_type_id_map[str(room_type.pms_id)] = room_type.id

                # Set up room type webhook
                self._set_up_room_type_webhook(
                    room_type_uuid=str(room_type.uuid),
                    room_type_pms_id=str(room_type.pms_id),
                    api_key=api_key,
                    callback_url=f"https://{current_site.domain}{reverse('pms:channex-availability-callback')}",
                )

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

    def _get_synced_rate_plans_restrictions(
        self,
        room_type_uuid: str,
        room_type_pms_id: str,
        start_date: str,
        end_date: str,
    ):
        """
        Get synced rate plans and restrictions

        Args:
            room_type_uuid (str): Room type id
            room_type_pms_id (str): Room type pms id
            start_date (str): Start date
            end_date (str): End date

        Returns:
            rate_plan_id_map (dict): Rate plan id map
            saved_restrictions (dict): Saved restrictions
        """

        room_type = RoomType.objects.get(uuid=room_type_uuid, pms_id=room_type_pms_id)
        synced_rate_plans = RatePlan.objects.filter(
            room_type=room_type
        ).prefetch_related(
            Prefetch(
                "restrictions",
                queryset=RatePlanRestrictions.objects.filter(
                    date__gte=start_date,
                    date__lte=end_date,
                ),
                to_attr="filtered_restrictions",
            )
        )

        rate_plan_id_map = {}
        saved_restrictions = {}
        for synced_rate_plan in synced_rate_plans:
            rate_plan_id_map[str(synced_rate_plan.pms_id)] = synced_rate_plan.id
            saved_restrictions[str(synced_rate_plan.pms_id)] = {}
            for restriction in synced_rate_plan.filtered_restrictions:
                date = restriction.date.strftime("%Y-%m-%d")
                saved_restrictions[str(synced_rate_plan.pms_id)][date] = {
                    # "availability": restriction.availability,
                    "rate": restriction.rate,
                }

        return rate_plan_id_map, saved_restrictions

    def _get_restrictions_to_update(
        self,
        room_type_uuid: str,
        payload: list[dict],
    ) -> tuple[list[dict], list[RatePlanRestrictions]]:
        # Nothing to update
        if len(payload) == 0:
            return [], []

        # We don't deal with changes that created by inventory_day mechanism
        inventory_day_date = timezone.now() + timezone.timedelta(
            days=self.hotel.inventory_days
        )
        if payload[0]["date"] == inventory_day_date.strftime("%Y-%m-%d"):
            # TODO: Log this
            return [], []

        date = set()
        for change in payload:
            date.add(change["date"])
        date_range = sorted(date)

        # Get rate plan id map and saved restrictions
        rate_plan_id_map, saved_restrictions = self._get_synced_rate_plans_restrictions(
            room_type_uuid=room_type_uuid,
            room_type_pms_id=payload[0]["room_type_id"],
            start_date=date_range[0],
            end_date=date_range[-1],
        )

        # Get data from Channex
        response = self.client.get_room_type_rate_plan_restrictions(
            property_pms_id=self.hotel.pms_id,
            date_from=date_range[0],
            date_to=date_range[-1],
            restrictions=["rate", "availability"],
        )
        if response.status_code != 200:
            raise Exception(response.json())
        channex_data = response.json().get("data")

        # Load rms_adapter
        self.load_rms_adapter()

        restriction_update_to_channex = []
        restriction_create_to_db = []
        # Loop through each synced rate plan
        for rate_plan_pms_id, rate_plan_id in rate_plan_id_map.items():
            # Loop through each date
            for date in date_range:
                original_rate_in_db = date in saved_restrictions[rate_plan_pms_id]

                # If original rate in db, use it, otherwise use channex data
                if original_rate_in_db:
                    original_rate = saved_restrictions[rate_plan_pms_id][date]["rate"]
                else:
                    original_rate = int(channex_data[rate_plan_pms_id][date]["rate"])

                new_rate = self.rms_adapter.calculate_rate(
                    date=timezone.datetime.strptime(date, "%Y-%m-%d").date(),
                    rate=int(original_rate),
                    availability=channex_data[rate_plan_pms_id][date]["availability"],
                )

                # If new rate is different from original rate, update it
                if new_rate != original_rate:
                    restriction_update_to_channex.append(
                        {
                            "property_id": str(self.hotel.pms_id),
                            "rate_plan_id": rate_plan_pms_id,
                            "date": date,
                            "rate": new_rate,
                        }
                    )

                    # If original rate is not in db, create it
                    if not original_rate_in_db:
                        restriction_create_to_db.append(
                            RatePlanRestrictions(
                                rate_plan_id=rate_plan_id,
                                date=date,
                                rate=original_rate,  # Original rate
                            )
                        )

        return restriction_update_to_channex, restriction_create_to_db

    def handle_trigger(self, room_type_uuid: str, payload: dict) -> bool:
        (
            restriction_update_to_channex,
            restriction_create_to_db,
        ) = self._get_restrictions_to_update(
            room_type_uuid=room_type_uuid,
            payload=payload,
        )

        if len(restriction_update_to_channex) > 0:
            response = self.client.update_room_type_rate_plan_restrictions(
                data=restriction_update_to_channex
            )
            if response.status_code != 200:
                raise Exception(response.json())
            RatePlanRestrictions.objects.bulk_create(restriction_create_to_db)
            return True

        return False
