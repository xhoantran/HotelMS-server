from datetime import datetime

from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.urls import reverse

from backend.pms.models import (
    Booking,
    BookingRoom,
    Hotel,
    RatePlan,
    RatePlanRestrictions,
    RoomType,
)
from backend.rms.tasks import handle_occupancy_based_trigger
from backend.utils.currency import get_currency_min_frac_size, is_valid_currency
from backend.utils.format import convert_to_obj

from ..client.channex import ChannexClient, ChannexClientAPIError
from ..models import (
    CMBookingConnector,
    CMHotelConnector,
    CMHotelConnectorAPIKey,
    CMRatePlanConnector,
    CMRoomTypeConnector,
)
from ..serializers import CMHotelConnectorSerializer


class ChannexException(Exception):
    pass


class ChannexAdapter:
    def __init__(self, cm_hotel_connector, *args, **kwargs):
        self.cm_hotel_connector: CMHotelConnector = convert_to_obj(
            cm_hotel_connector, CMHotelConnector
        )
        self.client = ChannexClient(api_key=self.cm_hotel_connector.cm_api_key)

    @staticmethod
    def validate_api_key(api_key: str):
        client = ChannexClient(api_key=api_key)
        try:
            client.list_properties()
        except ChannexClientAPIError:
            return False
        return True

    @staticmethod
    def validate_property_id(api_key: str, property_id: str):
        client = ChannexClient(api_key=api_key)
        try:
            client.get_property(property_id)
        except ChannexClientAPIError:
            return False
        return True

    def serialize_property_structure(self):
        try:
            room_type_rate_plan_map = {}
            data = self.client.list_rate_plans(
                property_id=self.cm_hotel_connector.cm_id
            )
            for rate_plan in data:
                room_type_rate_plan_map.setdefault(
                    rate_plan["attributes"]["room_type_id"], []
                ).append(
                    {
                        "cm_name": rate_plan["attributes"]["title"],
                        "cm_id": rate_plan["id"],
                    }
                )

            room_type_objects = []
            data = self.client.list_room_types(
                property_id=self.cm_hotel_connector.cm_id
            )
            for room_type in data:
                room_type_objects.append(
                    {
                        "cm_name": room_type["attributes"]["title"],
                        "cm_id": room_type["id"],
                        "cm_rate_plan_connectors": room_type_rate_plan_map.get(
                            room_type["id"], []
                        ),
                    }
                )

            data = self.client.get_property(self.cm_hotel_connector.cm_id)
            hotel = {
                "cm_name": data["attributes"]["title"],
                "cm_id": data["id"],
                "cm_room_type_connectors": room_type_objects,
                # PMS related fields
                "pms": {
                    "name": data["attributes"]["title"],
                    "address": data["attributes"]["address"],
                    "city": data["attributes"]["city"],
                    "country": data["attributes"]["country"],
                    "currency": data["attributes"]["currency"],
                    "timezone": data["attributes"]["timezone"],
                    "inventory_days": data["attributes"]["settings"]["state_length"],
                },
            }
            return CMHotelConnectorSerializer(hotel)
        except ChannexClientAPIError as e:
            raise ChannexException(e)

    @staticmethod
    def save_serialize_property_structure(
        serializer: CMHotelConnectorSerializer,
        cm_api_key: str,
    ):
        """
        Manually create hotel and its cm connectors to trigger signals and create
        all related objects
        """
        # Raise exception if currency is not supported
        is_valid_currency(serializer.data["pms"]["currency"])

        # Create hotel and its cm connectors
        hotel = Hotel.objects.create(
            name=serializer.data["pms"]["name"],
            address=serializer.data["pms"]["address"],
            city=serializer.data["pms"]["city"],
            country=serializer.data["pms"]["country"],
            currency=serializer.data["pms"]["currency"],
            timezone=serializer.data["pms"]["timezone"],
            inventory_days=serializer.data["pms"]["inventory_days"],
        )
        cm_hotel_connector = CMHotelConnector.objects.create(
            pms=hotel,
            channel_manager=CMHotelConnector.ChannelManagerChoices.CHANNEX,
            cm_name=serializer.data["cm_name"],
            cm_id=serializer.data["cm_id"],
            cm_api_key=cm_api_key,
        )

        for room_type_connector in serializer.data["cm_room_type_connectors"]:
            room_type = RoomType.objects.create(
                hotel=hotel,
                name=room_type_connector["cm_name"],
            )
            cm_room_type_connector = CMRoomTypeConnector.objects.create(
                cm_hotel_connector=cm_hotel_connector,
                pms=room_type,
                cm_name=room_type_connector["cm_name"],
                cm_id=room_type_connector["cm_id"],
            )
            for rate_plan_connector in room_type_connector["cm_rate_plan_connectors"]:
                rate_plan = RatePlan.objects.create(
                    room_type=room_type,
                    name=rate_plan_connector["cm_name"],
                )
                CMRatePlanConnector.objects.create(
                    cm_room_type_connector=cm_room_type_connector,
                    pms=rate_plan,
                    cm_name=rate_plan_connector["cm_name"],
                    cm_id=rate_plan_connector["cm_id"],
                )

        return cm_hotel_connector

    def get_all_upcoming_bookings(self, limit: int = 100) -> list[dict]:
        def _get_all_upcoming_bookings():
            try:
                page = 1
                while True:
                    data = self.client.list_bookings(
                        property_id=self.cm_hotel_connector.cm_id,
                        page=page,
                        limit=limit,
                    )
                    yield from data
                    if len(data) < limit:
                        break
                    page += 1
            except ChannexClientAPIError as e:
                raise ChannexException(e)

        return list(_get_all_upcoming_bookings())

    def get_room_type_id_map(self) -> dict[str, int]:
        """
        Base method
        """
        room_type_id = (
            CMRoomTypeConnector.objects.filter(
                pms__hotel__channel_manager_connector=self.cm_hotel_connector
            )
            .select_related("pms")
            .values_list("cm_id", "pms__id")
        )
        room_type_id_map = {"cm": {"None": None}, "pms": {"None": None}}
        for cm_id, pms_id in room_type_id:
            room_type_id_map["cm"][str(cm_id)] = pms_id
            room_type_id_map["pms"][pms_id] = str(cm_id)
        return room_type_id_map

    def get_rate_plan_id_map(self) -> dict[str, int]:
        """
        Base method
        """
        rate_plan_id = (
            CMRatePlanConnector.objects.filter(
                pms__room_type__hotel__channel_manager_connector=self.cm_hotel_connector
            )
            .select_related("pms")
            .values_list("cm_id", "pms__id")
        )
        rate_plan_id_map = {"cm": {"None": None}, "pms": {"None": None}}
        for cm_id, pms_id in rate_plan_id:
            rate_plan_id_map["cm"][str(cm_id)] = pms_id
            rate_plan_id_map["pms"][pms_id] = str(cm_id)
        return rate_plan_id_map

    def save_all_upcoming_bookings(self):
        room_type_id_map = self.get_room_type_id_map()

        new_bookings: list[Booking] = []
        new_cm_booking_connectors: list[CMBookingConnector] = []
        new_booking_rooms: list[BookingRoom] = []

        # Loop through all upcoming bookings
        for booking_data in self.get_all_upcoming_bookings():
            # Validate booking data
            assert booking_data["attributes"]["status"] in Booking.StatusChoices.values

            # Append booking object
            booking_obj = Booking(
                hotel=self.cm_hotel_connector.pms,
                dates=(
                    booking_data["attributes"]["arrival_date"],
                    booking_data["attributes"]["departure_date"],
                ),
                status=booking_data["attributes"]["status"],
                raw_data=booking_data,
            )
            new_bookings.append(booking_obj)

            # Map cm booking connector
            cm_booking_connector_obj = CMBookingConnector(
                cm_hotel_connector=self.cm_hotel_connector,
                cm_id=booking_data["id"],
                inserted_at=booking_data["attributes"]["inserted_at"],
            )
            cm_booking_connector_obj.booking_obj = booking_obj
            new_cm_booking_connectors.append(cm_booking_connector_obj)

            for room_data in booking_data["attributes"]["rooms"]:
                room_obj = BookingRoom(
                    room_type_id=room_type_id_map["cm"][str(room_data["room_type_id"])],
                    dates=(
                        room_data["checkin_date"],
                        room_data["checkout_date"],
                    ),
                    raw_data=room_data,
                )
                room_obj.booking_obj = booking_obj
                new_booking_rooms.append(room_obj)

        # Bulk create bookings
        Booking.objects.bulk_create(new_bookings)

        # Assign booking ids to cm booking connectors
        for cm_booking_connector_obj in new_cm_booking_connectors:
            cm_booking_connector_obj.pms_id = cm_booking_connector_obj.booking_obj.id
        CMBookingConnector.objects.bulk_create(new_cm_booking_connectors)

        # Assign booking ids to booking rooms
        for booking_room_obj in new_booking_rooms:
            booking_room_obj.booking_id = booking_room_obj.booking_obj.id
        BookingRoom.objects.bulk_create(new_booking_rooms)

    def get_prep_rate_plan_restrictions(
        self, new_rate_plan_restrictions: list[RatePlanRestrictions]
    ):
        rate_plan_id_map = self.get_rate_plan_id_map()
        currency_min_frac_size = get_currency_min_frac_size(
            self.cm_hotel_connector.pms.currency
        )
        cm_hotel_id = str(self.cm_hotel_connector.cm_id)

        rate_plan_restrictions = []
        for rate_plan_restriction in new_rate_plan_restrictions:
            rate_plan_restrictions.append(
                {
                    "property_id": cm_hotel_id,
                    "rate_plan_id": rate_plan_id_map["pms"][
                        rate_plan_restriction.rate_plan_id
                    ],
                    "date": rate_plan_restriction.date.strftime("%Y-%m-%d"),
                    "rate": rate_plan_restriction.rate * currency_min_frac_size,
                }
            )
        return rate_plan_restrictions

    def save_rate_plan_restrictions(self, new_rate_plan_restrictions):
        rate_plan_restrictions = self.get_prep_rate_plan_restrictions(
            new_rate_plan_restrictions
        )
        self.client.update_rate_plan_restrictions(rate_plan_restrictions)

    def save_booking_webhook(self):
        """
        Right now we only have 1 webhook per hotel, so it's not a big deal
        But if we have more than 1 webhook, we need to make sure that
        the API key will be rotated for all the webhooks
        """
        _, api_key = CMHotelConnectorAPIKey.objects.create_key(
            name=f"API key for {self.cm_hotel_connector.pms.name}",
            cm_hotel_connector=self.cm_hotel_connector,
        )
        current_site = Site.objects.get_current()
        self.client.update_or_create_webhook(
            property_id=str(self.cm_hotel_connector.cm_id),
            callback_url=f"https://{current_site.domain}{reverse('cm:webhook-booking')}",
            event_mask="booking_new,booking_modification,booking_cancellation",
            headers={"Authorization": "Api-Key " + api_key},
        )

    def _save_new_booking_revision(self, booking_cm_id, revision_cm_id):
        # Get revision data
        revision_data = self.client.get_booking_revision(revision_cm_id)

        # Get or create booking connector
        booking_connector = CMBookingConnector.objects.create(
            cm_hotel_connector=self.cm_hotel_connector,
            cm_id=booking_cm_id,
            # TODO: Naive datetime. Check if UTC or not
            inserted_at=revision_data["attributes"]["inserted_at"],
        )

        # Validate revision data
        assert revision_data["attributes"]["booking_id"] == booking_cm_id
        assert revision_data["id"] == revision_cm_id
        assert revision_data["attributes"]["status"] == Booking.StatusChoices.NEW

        # Create booking
        booking = Booking.objects.create(
            hotel=self.cm_hotel_connector.pms,
            dates=(
                revision_data["attributes"]["arrival_date"],
                revision_data["attributes"]["departure_date"],
            ),
            status="new",
            raw_data=revision_data,
        )

        # Assign booking id to booking connector
        booking_connector.pms = booking
        booking_connector.save()

        # Create booking rooms
        affected_room_types = set()
        room_type_id_map = self.get_room_type_id_map()
        booking_rooms = []
        for room_data in revision_data["attributes"]["rooms"]:
            room_type_pms_id = room_type_id_map["cm"][str(room_data["room_type_id"])]
            affected_room_types.add(room_type_pms_id)
            booking_room = BookingRoom(
                booking=booking,
                room_type_id=room_type_pms_id,
                dates=(
                    room_data["checkin_date"],
                    room_data["checkout_date"],
                ),
                raw_data=room_data,
            )
            booking_rooms.append(booking_room)
        BookingRoom.objects.bulk_create(booking_rooms)

        # Trigger occupancy update
        handle_occupancy_based_trigger.delay(
            hotel_id=self.cm_hotel_connector.pms.id,
            room_types=list(affected_room_types),
            dates=(
                revision_data["attributes"]["arrival_date"],
                revision_data["attributes"]["departure_date"],
            ),
        )

    def _save_modified_booking_revision(self, booking_cm_id, revision_cm_id):
        # Get revision data
        revision_data = self.client.get_booking_revision(revision_cm_id)

        # Get booking connector and its booking
        booking_connector = CMBookingConnector.objects.get(
            cm_hotel_connector=self.cm_hotel_connector,
            cm_id=booking_cm_id,
        )
        booking = booking_connector.pms

        # Validate revision data
        assert revision_data["attributes"]["booking_id"] == booking_cm_id
        assert revision_data["id"] == revision_cm_id
        assert revision_data["attributes"]["status"] == Booking.StatusChoices.MODIFIED
        assert booking.status in (
            Booking.StatusChoices.NEW,
            Booking.StatusChoices.MODIFIED,
        )

        old_arrival_date = booking.dates.lower
        old_departure_date = booking.dates.upper

        # Update booking status
        booking.status = Booking.StatusChoices.MODIFIED
        booking.dates = (
            revision_data["attributes"]["arrival_date"],
            revision_data["attributes"]["departure_date"],
        )
        booking.raw_data = revision_data
        booking.save()

        # Update booking rooms
        affected_room_types = set()
        room_type_id_map = self.get_room_type_id_map()
        booking_rooms = []
        for room_data in revision_data["attributes"]["rooms"]:
            room_type_pms_id = room_type_id_map["cm"][str(room_data["room_type_id"])]
            affected_room_types.add(room_type_pms_id)
            booking_room = BookingRoom.objects.create(
                booking=booking,
                room_type_id=room_type_pms_id,
                dates=(
                    room_data["checkin_date"],
                    room_data["checkout_date"],
                ),
                raw_data=room_data,
            )
            booking_rooms.append(booking_room)

        # Get existing booking rooms to get affected room types and delete them
        existing_booking_rooms = BookingRoom.objects.filter(booking=booking)
        for existing_booking_room in existing_booking_rooms:
            affected_room_types.add(existing_booking_room.room_type_id)
        existing_booking_rooms.delete()

        # Create new booking rooms
        BookingRoom.objects.bulk_create(booking_rooms)

        # Maximize affected dates
        affected_start_date = min(
            old_arrival_date,
            datetime.strptime(
                revision_data["attributes"]["arrival_date"],
                "%Y-%m-%d",
            ).date(),
        )
        affected_end_date = max(
            old_departure_date,
            datetime.strptime(
                revision_data["attributes"]["departure_date"],
                "%Y-%m-%d",
            ).date(),
        )

        # Trigger occupancy update
        handle_occupancy_based_trigger.delay(
            hotel_id=self.cm_hotel_connector.pms.id,
            room_types=list(affected_room_types),
            dates=(
                datetime.strftime(affected_start_date, "%Y-%m-%d"),
                datetime.strftime(affected_end_date, "%Y-%m-%d"),
            ),
        )

    def _save_cancelled_booking_revision(self, booking_cm_id, revision_cm_id):
        # Get revision data
        revision_data = self.client.get_booking_revision(revision_cm_id)

        # Get booking connector and its booking
        booking_connector = CMBookingConnector.objects.get(
            cm_hotel_connector=self.cm_hotel_connector,
            cm_id=booking_cm_id,
        )
        booking = booking_connector.pms

        # Validate revision data
        assert revision_data["attributes"]["booking_id"] == booking_cm_id
        assert revision_data["id"] == revision_cm_id
        assert revision_data["attributes"]["status"] == Booking.StatusChoices.CANCELLED
        assert booking.status in (
            Booking.StatusChoices.NEW,
            Booking.StatusChoices.MODIFIED,
        )

        # Update booking status
        booking.status = Booking.StatusChoices.CANCELLED
        booking.save()

        # Get affected room types
        booking_rooms = BookingRoom.objects.filter(booking=booking)
        affected_room_types = booking_rooms.values_list("room_type__id", flat=True)

        # Trigger occupancy update
        handle_occupancy_based_trigger.delay(
            hotel_id=self.cm_hotel_connector.pms.id,
            room_types=list(affected_room_types),
            dates=(
                datetime.strftime(booking.dates.lower, "%Y-%m-%d"),
                datetime.strftime(booking.dates.upper, "%Y-%m-%d"),
            ),
        )

    def save_booking_revision(self, data):
        if str(self.cm_hotel_connector.cm_id) != data["property_id"]:
            raise ValidationError("Invalid property ID")

        event = data.get("event", None)
        if event == "booking_new":
            self._save_new_booking_revision(
                booking_cm_id=data["payload"]["booking_id"],
                revision_cm_id=data["payload"]["booking_revision_id"],
            )
        elif event == "booking_modification":
            self._save_modified_booking_revision(
                booking_cm_id=data["payload"]["booking_id"],
                revision_cm_id=data["payload"]["booking_revision_id"],
            )
        elif event == "booking_cancellation":
            self._save_cancelled_booking_revision(
                booking_cm_id=data["payload"]["booking_id"],
                revision_cm_id=data["payload"]["booking_revision_id"],
            )
        elif event == "booking":
            pass
        else:
            raise ValidationError("Unknown event type")
