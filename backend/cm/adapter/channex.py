from django.contrib.sites.models import Site
from django.db.models import Q
from django.urls import reverse

from backend.pms.models import RatePlan, RoomType
from backend.utils.currency import get_currency_min_frac_size, is_valid_currency
from backend.utils.format import convert_to_obj

from ..client.channex import ChannexClient, ChannexClientAPIError
from ..models import CMHotel


class ChannexException(Exception):
    pass


class ChannexCMAdapter:
    def __init__(self, cm_hotel, *args, **kwargs):
        self.cm_hotel: CMHotel = convert_to_obj(cm_hotel, CMHotel)
        self.hotel = self.cm_hotel.hotel
        self.client = ChannexClient(api_key=self.cm_hotel.cm_api_key)

    @staticmethod
    def validate_api_key(api_key: str):
        client = ChannexClient(api_key=api_key)
        try:
            client.get_properties()
        except ChannexClientAPIError:
            return False
        return True

    @staticmethod
    def validate_cm_id(api_key: str, cm_id: str):
        client = ChannexClient(api_key=api_key)
        try:
            client.get_property(cm_id)
        except ChannexClientAPIError:
            return False
        return True

    # TODO: Create a wrapper function for sync_up to handle exceptions (retry, etc.)
    def sync_up(self, api_key: str):
        # Get properties
        response = self.client.get_property(self.hotel.cm_id)
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
        data = self.client.get_room_types(property_id=self.hotel.cm_id)
        room_type_cm_ids = []
        room_type_objects = []

        # Create room types
        for room_type in data:
            room_type_objects.append(
                RoomType(
                    name=room_type["attributes"]["title"],
                    cm_id=room_type["id"],
                    hotel=self.hotel,
                )
            )
            room_type_cm_ids.append(room_type["id"])
        room_types = RoomType.objects.bulk_create(
            room_type_objects,
            update_conflicts=True,
            update_fields=["name"],
            unique_fields=["cm_id", "hotel"],
        )
        RoomType.objects.filter(
            ~Q(cm_id__in=room_type_cm_ids) & Q(hotel=self.hotel)
        ).delete()

        # If hotel has no room type, we are done
        if len(room_types) == 0:
            return

        # If bulk_create not return id
        if room_types[0].id is None:
            room_types = RoomType.objects.filter(
                cm_id__in=room_type_cm_ids, hotel=self.hotel
            )

        current_site = Site.objects.get_current()
        # # Set up room type webhook
        # self.client.update_or_create_webhook(
        #     property_id=str(self.hotel.cm_id),
        #     callback_url=f"https://{current_site.domain}{reverse('cm:channex-availability-callback')}",
        #     event_mask=f"ari:booked:{str(room_type.cm_id)}:*",
        #     request_params={"room_type_uuid": str(room_type.uuid)},
        #     headers={"Authorization": f"Api-Key {api_key}"},
        # )

        room_type_id_map = {}
        for room_type in room_types:
            # Create room type id map
            room_type_id_map[str(room_type.cm_id)] = room_type.id

        # Get rate plans
        data = self.client.get_rate_plans(property_id=self.hotel.cm_id)

        # Create rate plans
        rate_plan_cm_ids = []
        rate_plan_objects = []
        for rate_plan in data:
            rate_plan_objects.append(
                RatePlan(
                    name=rate_plan["attributes"]["title"],
                    cm_id=rate_plan["id"],
                    # using room_type_id_map to get the id of the room type
                    room_type_id=room_type_id_map[
                        rate_plan["attributes"]["room_type_id"]
                    ],
                )
            )
            rate_plan_cm_ids.append(rate_plan["id"])
        RatePlan.objects.bulk_create(
            rate_plan_objects,
            update_conflicts=True,
            update_fields=["name"],
            unique_fields=["cm_id", "room_type_id"],
        )
        RatePlan.objects.filter(
            ~Q(cm_id__in=rate_plan_cm_ids) & Q(room_type__hotel=self.hotel)
        ).delete()

    # def handle_booked_ari_trigger(self, room_type_uuid: str, payload: dict):
    #     # Nothing to update
    #     if len(payload) == 0:
    #         return

    #     # We don't deal with changes that created by inventory_day mechanism
    #     if payload[0]["date"] == self.get_last_inventory_date():
    #         return

    #     (
    #         restriction_update_to_channex,
    #         restriction_create_to_db,
    #     ) = self.get_restrictions_to_update(
    #         room_type_uuid=[room_type_uuid],
    #         room_type_cm_id=payload[0]["room_type_id"],
    #         sorted_date_range=self._get_date_range(payload),
    #     )
    #     mail_admins(
    #         "Occupancy Trigger",
    #         f"Hotel: {self.hotel.name}\n"
    #         f"Restriction update to channex: {restriction_update_to_channex}",
    #     )
    #     if len(restriction_update_to_channex) > 0:
    #         response = self.client.update_room_type_rate_plan_restrictions(
    #             data=restriction_update_to_channex
    #         )
    #         if response.status_code != 200:
    #             raise Exception(response.json())
    #         RatePlanRestrictions.objects.bulk_create(restriction_create_to_db)

    # def handle_time_based_trigger(self, date: date_class):
    #     # List is important
    #     room_type_uuid = RoomType.objects.filter(hotel=self.hotel).values_list(
    #         "uuid", flat=True
    #     )
    #     (
    #         restriction_update_to_channex,
    #         restriction_create_to_db,
    #     ) = self.get_restrictions_to_update(
    #         room_type_uuid=room_type_uuid,
    #         room_type_cm_id=None,
    #         sorted_date_range=[date.strftime("%Y-%m-%d")],
    #     )
    #     mail_admins(
    #         "Time Trigger",
    #         f"Hotel: {self.hotel.name}\n"
    #         f"Restriction update to channex: {restriction_update_to_channex}",
    #     )

    #     if len(restriction_update_to_channex) > 0:
    #         response = self.client.update_room_type_rate_plan_restrictions(
    #             data=restriction_update_to_channex
    #         )
    #         if response.status_code != 200:
    #             raise Exception(response.json())
    #         RatePlanRestrictions.objects.bulk_create(restriction_create_to_db)
