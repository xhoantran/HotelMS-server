import uuid
from datetime import date as date_class

from django.contrib.sites.models import Site
from django.core.mail import mail_admins
from django.db.models import Prefetch, Q
from django.db.models.query import QuerySet
from django.urls import reverse
from django.utils import timezone

from backend.rms.adapter import DynamicPricingAdapter
from backend.utils.channex_client import ChannexClient
from backend.utils.currency import get_currency_min_frac_size, is_valid_currency

from ..models import RatePlan, RatePlanRestrictions, RoomType
from .base import PMSBaseAdapter


class ChannexException(Exception):
    pass


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

    def sync_up(self, api_key: str):
        # Get properties
        response = self.client.get_property(self.hotel.pms_id)
        if response.status_code != 200:
            raise Exception(response.json())
        data = response.json().get("data")
        self.hotel.name = data["attributes"]["title"]
        self.hotel.address = data["attributes"]["address"]
        self.hotel.city = data["attributes"]["city"]
        self.hotel.country = data["attributes"]["country"]
        self.hotel.currency = data["attributes"]["currency"]
        is_valid_currency(self.hotel.currency)  # Check if currency is valid
        self.hotel.timezone = data["attributes"]["timezone"]
        self.hotel.inventory_days = data["attributes"]["settings"]["state_length"]
        self.hotel.save()

        # Get room types and rate plans
        data = self.client.get_room_types(property_id=self.hotel.pms_id)
        room_type_pms_ids = []
        room_type_objects = []

        # Create room types
        for room_type in data:
            room_type_objects.append(
                RoomType(
                    name=room_type["attributes"]["title"],
                    pms_id=room_type["id"],
                    hotel=self.hotel,
                )
            )
            room_type_pms_ids.append(room_type["id"])
        room_types = RoomType.objects.bulk_create(
            room_type_objects,
            update_conflicts=True,
            update_fields=["name"],
            unique_fields=["pms_id", "hotel"],
        )
        RoomType.objects.filter(
            ~Q(pms_id__in=room_type_pms_ids) & Q(hotel=self.hotel)
        ).delete()

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
                self.client.update_or_create_webhook(
                    property_id=str(self.hotel.pms_id),
                    callback_url=f"https://{current_site.domain}{reverse('pms:channex-availability-callback')}",
                    event_mask=f"ari:booked:{str(room_type.pms_id)}:*",
                    request_params={"room_type_uuid": str(room_type.uuid)},
                    headers={"Authorization": f"Api-Key {api_key}"},
                )

            # Get rate plans
            data = self.client.get_rate_plans(property_id=self.hotel.pms_id)

            # Create rate plans
            rate_plan_pms_ids = []
            rate_plan_objects = []
            for rate_plan in data:
                rate_plan_objects.append(
                    RatePlan(
                        name=rate_plan["attributes"]["title"],
                        pms_id=rate_plan["id"],
                        # using room_type_id_map to get the id of the room type
                        room_type_id=room_type_id_map[
                            rate_plan["attributes"]["room_type_id"]
                        ],
                    )
                )
                rate_plan_pms_ids.append(rate_plan["id"])
            RatePlan.objects.bulk_create(
                rate_plan_objects,
                update_conflicts=True,
                update_fields=["name"],
                unique_fields=["pms_id", "room_type_id"],
            )
            RatePlan.objects.filter(
                ~Q(pms_id__in=rate_plan_pms_ids) & Q(room_type__hotel=self.hotel)
            ).delete()

    def _get_synced_rate_plans_restrictions(
        self,
        room_type_uuid: str | uuid.UUID | QuerySet,
        room_type_pms_id: str | uuid.UUID | None,
        start_date: str,
        end_date: str,
    ):
        """
        Get synced rate plans and restrictions. We use this for both occupancy trigger
        and time trigger.

        Args:
            room_type_uuid (str | uuid.UUID | QuerySet): Room type uuid
            room_type_pms_id (str | uuid.UUID | None): Room type pms id
            start_date (str): Start date
            end_date (str): End date

        Returns:
            rate_plan_id_map (dict): Rate plan id map
            saved_restrictions (dict): Saved restrictions
        """
        if isinstance(room_type_uuid, (str, uuid.UUID)) and isinstance(
            room_type_pms_id, (str, uuid.UUID)
        ):
            synced_rate_plans = RatePlan.objects.filter(
                room_type__uuid=room_type_uuid,
                room_type__pms_id=room_type_pms_id,
                room_type__hotel=self.hotel,
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
        elif isinstance(room_type_uuid, QuerySet):
            synced_rate_plans = RatePlan.objects.filter(
                room_type__uuid__in=room_type_uuid,
                room_type__hotel=self.hotel,
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
        else:
            raise ChannexException(
                "Either provide room_type_uuid and room_type_pms_id or just room_type_uuid list"
            )

        rate_plan_id_map = {}
        saved_restrictions = {}
        for synced_rate_plan in synced_rate_plans:
            rate_plan_id_map[str(synced_rate_plan.pms_id)] = synced_rate_plan.id
            saved_restrictions[str(synced_rate_plan.pms_id)] = {}
            for restriction in synced_rate_plan.filtered_restrictions:
                date = restriction.date.strftime("%Y-%m-%d")
                saved_restrictions[str(synced_rate_plan.pms_id)][date] = {
                    "rate": restriction.rate
                }

        return rate_plan_id_map, saved_restrictions

    def _get_last_inventory_days(self):
        """
        Get last inventory days

        Returns:
            last_inventory_days (int): Last inventory days
        """
        return (
            timezone.now() + timezone.timedelta(days=self.hotel.inventory_days - 1)
        ).strftime("%Y-%m-%d")

    @staticmethod
    def _get_date_range(payload: list[dict]):
        """
        Get date range

        Args:
            payload (list): Payload

        Returns:
            date_range (list): Date range
        """
        date = set()
        for change in payload:
            date.add(change["date"])
        return sorted(date)

    def _get_restrictions_to_update(
        self,
        room_type_uuid: str | list[str],
        room_type_pms_id: str | None,
        sorted_date_range: list[str],
    ) -> tuple[list[dict], list[RatePlanRestrictions]]:
        # Get rate plan id map and saved restrictions
        rate_plan_id_map, saved_restrictions = self._get_synced_rate_plans_restrictions(
            room_type_uuid=room_type_uuid,
            room_type_pms_id=room_type_pms_id,
            start_date=sorted_date_range[0],
            end_date=sorted_date_range[-1],
        )

        # Get data from Channex
        response = self.client.get_room_type_rate_plan_restrictions(
            property_pms_id=self.hotel.pms_id,
            date_from=sorted_date_range[0],
            date_to=sorted_date_range[-1],
            restrictions=["rate", "booked"],
        )
        if response.status_code != 200:
            raise Exception(response.json())
        channex_data = response.json().get("data")

        # Load rms_adapter
        self.load_rms_adapter()

        restriction_update_to_channex = []
        restriction_create_to_db = []
        current_datetime = timezone.now()
        currency_min_frac_size = get_currency_min_frac_size(self.hotel.currency)
        # Loop through each synced rate plan
        for rate_plan_pms_id, rate_plan_id in rate_plan_id_map.items():
            # Loop through each date
            for date in sorted_date_range:
                # The original rate on that date for that rate plan in db?
                original_rate_in_db = date in saved_restrictions[rate_plan_pms_id]

                try:
                    # If original rate in db, use it, otherwise use channex data
                    if original_rate_in_db:
                        original_rate = saved_restrictions[rate_plan_pms_id][date][
                            "rate"
                        ]
                    else:
                        original_rate = int(
                            channex_data[rate_plan_pms_id][date]["rate"]
                        )
                    new_rate = (
                        self.rms_adapter.calculate_rate(
                            rate=int(original_rate),
                            date=timezone.datetime.strptime(date, "%Y-%m-%d").date(),
                            current_datetime=current_datetime,
                            occupancy=channex_data[rate_plan_pms_id][date]["booked"],
                        )
                        * currency_min_frac_size
                    )
                # Unsynced rate plan
                except KeyError as e:
                    if e.args[0] == rate_plan_pms_id:
                        unsynced_rate_plan = RatePlan.objects.get(
                            room_type__hotel=self.hotel,
                            pms_id=rate_plan_pms_id,
                        )
                        mail_admins(
                            "Channex Sync Error",
                            f"Rate plan {unsynced_rate_plan.name} ({unsynced_rate_plan.room_type.hotel.name}"
                            f" - {unsynced_rate_plan.room_type.name}) is not on Channex anymore but it is still in"
                            " RMS. Please sync it manually. \nIf you believe this is an error, please contact our support team.",
                        )
                        continue
                    else:
                        raise e

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

    def handle_booked_ari_trigger(self, room_type_uuid: str, payload: dict):
        # Nothing to update
        if len(payload) == 0:
            return

        # We don't deal with changes that created by inventory_day mechanism
        if payload[0]["date"] == self._get_last_inventory_days():
            return

        (
            restriction_update_to_channex,
            restriction_create_to_db,
        ) = self._get_restrictions_to_update(
            room_type_uuid=room_type_uuid,
            room_type_pms_id=payload[0]["room_type_id"],
            sorted_date_range=self._get_date_range(payload),
        )
        mail_admins(
            "Occupancy Trigger",
            f"Hotel: {self.hotel.name}\n"
            f"Restriction update to channex: {restriction_update_to_channex}",
        )
        if len(restriction_update_to_channex) > 0:
            response = self.client.update_room_type_rate_plan_restrictions(
                data=restriction_update_to_channex
            )
            if response.status_code != 200:
                raise Exception(response.json())
            RatePlanRestrictions.objects.bulk_create(restriction_create_to_db)

    def handle_time_based_trigger(self, date: date_class):
        # List is important
        room_type_uuid = RoomType.objects.filter(hotel=self.hotel).values_list(
            "uuid", flat=True
        )
        (
            restriction_update_to_channex,
            restriction_create_to_db,
        ) = self._get_restrictions_to_update(
            room_type_uuid=room_type_uuid,
            room_type_pms_id=None,
            sorted_date_range=[date.strftime("%Y-%m-%d")],
        )
        mail_admins(
            "Time Trigger",
            f"Hotel: {self.hotel.name}\n"
            f"Restriction update to channex: {restriction_update_to_channex}",
        )

        if len(restriction_update_to_channex) > 0:
            response = self.client.update_room_type_rate_plan_restrictions(
                data=restriction_update_to_channex
            )
            if response.status_code != 200:
                raise Exception(response.json())
            RatePlanRestrictions.objects.bulk_create(restriction_create_to_db)
