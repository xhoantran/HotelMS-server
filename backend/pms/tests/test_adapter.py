import uuid
import zoneinfo

import pytest
from django.utils import timezone

from backend.utils.format import convert_to_id

from ..adapter import (
    ChannexPMSAdapter,
    DefaultPMSAdapter,
    PMSBaseAdapter,
    RoomTypeAdapter,
)
from ..models import RatePlan, RatePlanRestrictions, RoomType


class TestRoomTypeAdapter:
    def test_room_type_get_rooms(self, db, room_type_factory, room_factory):
        room_type = room_type_factory()
        room_factory.create_batch(3, room_type=room_type)
        assert room_type.rooms.count() == 3

    def test_room_type_booked_rooms(
        self,
        db,
        django_assert_num_queries,
        room_type_factory,
        room_factory,
        booking_factory,
    ):
        room_type = room_type_factory()
        room = room_factory.create_batch(40, room_type=room_type)[0]
        bookings = booking_factory.create_batch(2, room=room)
        room_type_adapter = RoomTypeAdapter(room_type)
        with django_assert_num_queries(1):
            booked_room = room_type_adapter.count_booked_rooms(
                start_date=bookings[0].start_date,
                end_date=bookings[1].end_date,
            )
            assert booked_room == 1
        with pytest.raises(ValueError):
            room_type_adapter.count_booked_rooms(
                start_date=bookings[1].end_date,
                end_date=bookings[0].start_date,
            )
        start_date = str(bookings[0].start_date)
        assert room_type_adapter.count_booked_rooms(start_date=start_date) == 1

    def test_room_type_available_rooms(
        self,
        db,
        django_assert_max_num_queries,
        room_type_factory,
        room_factory,
        booking_factory,
    ):
        room_type = room_type_factory()
        room = room_factory.create_batch(40, room_type=room_type)[0]
        bookings = booking_factory.create_batch(2, room=room)
        room_type_adapter = RoomTypeAdapter(room_type)
        with django_assert_max_num_queries(1):
            assert room_type_adapter.count_available_rooms(bookings[0].start_date) == 39
        assert room_type_adapter.is_available(
            start_date=bookings[0].start_date,
            end_date=bookings[1].end_date,
        )
        assert (
            room_type_adapter.count_available_rooms(
                start_date=bookings[0].start_date,
                end_date=bookings[0].start_date,
            )
            == 39
        )

    def test_get_available_room(
        self, db, room_type_factory, room_factory, booking_factory
    ):
        room_type = room_type_factory()
        rooms = room_factory.create_batch(2, room_type=room_type)
        booking_factory.reset_sequence(0)
        booking_factory(room=rooms[0])
        room_type_adapter = RoomTypeAdapter(room_type)
        available_room = room_type_adapter.get_available_room(
            start_date=timezone.localtime(),
            end_date=timezone.localtime() + timezone.timedelta(days=20),
        )
        assert available_room == rooms[1]

    def test_booking_total_rate(self, db, booking_factory):
        booking = booking_factory()
        assert booking.total_rate == booking.rate * booking.number_of_nights


def test_pms_base_adapter(hotel_factory):
    hotel = hotel_factory()
    adapter = PMSBaseAdapter(hotel)
    assert adapter.hotel == hotel

    adapter = PMSBaseAdapter(hotel=hotel.id)
    assert adapter.hotel == hotel

    assert convert_to_id(hotel.id, type(hotel)) == hotel.id

    with pytest.raises(TypeError):
        convert_to_id(object(), type(hotel))

    with pytest.raises(TypeError):
        PMSBaseAdapter(hotel=object())

    with pytest.raises(NotImplementedError):
        adapter.get_rate_plans()

    with pytest.raises(NotImplementedError):
        adapter.get_room_types()


class TestDefaultPMSAdapter:
    def test_get_rate_plans(self, hotel_factory, room_type_factory, rate_plan_factory):
        hotel = hotel_factory()
        room_type = room_type_factory(hotel=hotel)
        rate_plan_factory.create_batch(2, room_type=room_type)
        adapter = DefaultPMSAdapter(hotel)
        assert adapter.get_rate_plans().count() == 2
        assert adapter.get_rate_plans(room_type=room_type).count() == 2
        assert adapter.get_rate_plans(room_type=room_type.id).count() == 2

    def test_get_room_types(self, hotel_factory, room_type_factory):
        hotel = hotel_factory()
        room_type_factory.create_batch(2, hotel=hotel)
        adapter = DefaultPMSAdapter(hotel)
        assert adapter.get_room_types().count() == 2


class TestChannexPMSAdapter:
    def test_init(self, mocked_channex_validation, hotel_factory):
        hotel = hotel_factory(channex=True)
        adapter = ChannexPMSAdapter(hotel)
        assert adapter.hotel == hotel

    def test_sync_up(
        self,
        mocker,
        mocked_channex_validation,
        hotel_factory,
    ):
        mocker.patch(
            "backend.utils.channex_client.ChannexClient._get_room_types",
            return_value=mocker.Mock(
                status_code=200,
                json=mocker.Mock(
                    return_value={
                        "data": [
                            {
                                "attributes": {
                                    "id": "877d2bd2-74a0-4d77-ad1c-a69ae0cee94d",
                                    "title": "Double Room",
                                },
                                "id": "877d2bd2-74a0-4d77-ad1c-a69ae0cee94d",
                                "type": "room_type",
                            }
                        ]
                    }
                ),
            ),
        )
        mocker.patch(
            "backend.utils.channex_client.ChannexClient._get_rate_plans",
            return_value=mocker.Mock(
                status_code=200,
                json=mocker.Mock(
                    return_value={
                        "data": [
                            {
                                "attributes": {
                                    "id": "3285e794-c11e-4089-9a3b-77294a85c2c5",
                                    "room_type_id": "877d2bd2-74a0-4d77-ad1c-a69ae0cee94d",
                                    "title": "Standard Rate",
                                },
                                "id": "3285e794-c11e-4089-9a3b-77294a85c2c5",
                                "type": "rate_plan",
                            },
                            {
                                "attributes": {
                                    "id": "dd1e2ead-b503-4289-a57e-ad51184fafbe",
                                    "room_type_id": "877d2bd2-74a0-4d77-ad1c-a69ae0cee94d",
                                    "title": "Non Refundable Rate",
                                },
                                "id": "dd1e2ead-b503-4289-a57e-ad51184fafbe",
                                "type": "rate_plan",
                            },
                            {
                                "attributes": {
                                    "id": "0c9a0fba-71f3-4da4-af98-f9f036923dd8",
                                    "room_type_id": "877d2bd2-74a0-4d77-ad1c-a69ae0cee94d",
                                    "title": "Non Refundable Rate",
                                },
                                "id": "0c9a0fba-71f3-4da4-af98-f9f036923dd8",
                                "type": "rate_plan",
                            },
                        ]
                    }
                ),
            ),
        )
        hotel = hotel_factory(channex=True)
        assert RoomType.objects.filter(hotel=hotel).count() == 1
        assert RatePlan.objects.filter(room_type__hotel=hotel).count() == 3

        mocker.patch(
            "backend.utils.channex_client.ChannexClient._get_rate_plans",
            return_value=mocker.Mock(
                status_code=401,
                json=mocker.Mock(
                    return_value={
                        "errors": "Some error",
                    }
                ),
            ),
        )
        with pytest.raises(Exception):
            ChannexPMSAdapter(hotel).sync_up()

        mocker.patch(
            "backend.utils.channex_client.ChannexClient.get_property",
            return_value=mocker.Mock(
                status_code=401,
            ),
        )
        with pytest.raises(Exception):
            ChannexPMSAdapter(hotel).sync_up()

    def test_get_synced_rate_plans_restrictions(
        self,
        mocked_channex_validation,
        hotel_factory,
        room_type_factory,
        rate_plan_factory,
        rate_plan_restrictions_factory,
        django_assert_num_queries,
    ):
        hotel = hotel_factory(channex=True)
        room_type = room_type_factory(hotel=hotel)
        rate_plans = rate_plan_factory.create_batch(10, room_type=room_type)
        for rate_plan in rate_plans:
            rate_plan_restrictions_factory(rate_plan=rate_plan, date="2020-01-01")
        adapter = ChannexPMSAdapter(room_type.hotel)
        with django_assert_num_queries(2):
            (
                rate_plan_id_map,
                saved_restrictions,
            ) = adapter._get_synced_rate_plans_restrictions(
                room_type_uuid=room_type.uuid,
                room_type_pms_id=room_type.pms_id,
                start_date="2020-01-01",
                end_date="2020-01-31",
            )
            assert len(rate_plan_id_map) == 10
            assert len(saved_restrictions) == 10
            for value in saved_restrictions.values():
                assert len(value) == 1

    def test_get_restrictions_to_update(
        self,
        mocked_channex_validation,
        mocker,
        hotel_factory,
        occupancy_based_rule_factory,
    ):
        mocker.patch(
            "backend.utils.channex_client.ChannexClient._get_room_types",
            return_value=mocker.Mock(
                status_code=200,
                json=mocker.Mock(
                    return_value={
                        "data": [
                            {
                                "attributes": {
                                    "id": "877d2bd2-74a0-4d77-ad1c-a69ae0cee94d",
                                    "title": "Standard Room",
                                },
                                "id": "877d2bd2-74a0-4d77-ad1c-a69ae0cee94d",
                                "type": "room_type",
                            }
                        ]
                    }
                ),
            ),
        )
        mocker.patch(
            "backend.utils.channex_client.ChannexClient._get_rate_plans",
            return_value=mocker.Mock(
                status_code=200,
                json=mocker.Mock(
                    # Removed unnecessary fields
                    return_value={
                        "data": [
                            {
                                "attributes": {
                                    "id": "3285e794-c11e-4089-9a3b-77294a85c2c5",
                                    "room_type_id": "877d2bd2-74a0-4d77-ad1c-a69ae0cee94d",
                                    "title": "Standard Rate",
                                },
                                "id": "3285e794-c11e-4089-9a3b-77294a85c2c5",
                                "type": "rate_plan",
                            },
                            {
                                "attributes": {
                                    "id": "dd1e2ead-b503-4289-a57e-ad51184fafbe",
                                    "room_type_id": "877d2bd2-74a0-4d77-ad1c-a69ae0cee94d",
                                    "title": "Non Refundable Rate",
                                },
                                "id": "dd1e2ead-b503-4289-a57e-ad51184fafbe",
                                "type": "rate_plan",
                            },
                        ]
                    }
                ),
            ),
        )
        hotel = hotel_factory(channex=True)
        assert RoomType.objects.filter(hotel=hotel).count() == 1
        assert RatePlan.objects.filter(room_type__hotel=hotel).count() == 2
        RatePlanRestrictions.objects.create(
            rate_plan=RatePlan.objects.get(
                pms_id="3285e794-c11e-4089-9a3b-77294a85c2c5"
            ),
            date="2023-09-02",
            rate=500000,
        )
        RatePlanRestrictions.objects.create(
            rate_plan=RatePlan.objects.get(
                pms_id="dd1e2ead-b503-4289-a57e-ad51184fafbe"
            ),
            date="2023-09-02",
            rate=600000,
        )

        adapter = ChannexPMSAdapter(hotel)

        # Set up rules
        setting = hotel.dynamic_pricing_setting
        setting.is_occupancy_based = True
        setting.save()

        # Create rules
        occupancy_based_rule_factory(
            setting=setting,
            increment_factor=200000,
            min_occupancy=10,
        )
        occupancy_based_rule_factory(
            setting=setting,
            increment_factor=250000,
            min_occupancy=11,
        )

        # Activate rules
        adapter.load_rms_adapter()

        mocker.patch(
            "backend.utils.channex_client.ChannexClient.get_room_type_rate_plan_restrictions",
            return_value=mocker.Mock(
                status_code=200,
                json=mocker.Mock(
                    return_value={
                        "data": {
                            "3285e794-c11e-4089-9a3b-77294a85c2c5": {
                                "2023-09-01": {"booked": 10, "rate": "500000"},
                                "2023-09-02": {"booked": 11, "rate": "700000"},
                            },
                            "dd1e2ead-b503-4289-a57e-ad51184fafbe": {
                                "2023-09-01": {"booked": 10, "rate": "600000"},
                                "2023-09-02": {"booked": 11, "rate": "800000"},
                            },
                        }
                    }
                ),
            ),
        )
        payload = [
            {
                "booked": 11,
                "date": "2023-09-01",
                "rate_plan_id": "dd1e2ead-b503-4289-a57e-ad51184fafbe",
                "room_type_id": "877d2bd2-74a0-4d77-ad1c-a69ae0cee94d",
            },
            {
                "booked": 11,
                "date": "2023-09-01",
                "rate_plan_id": "3285e794-c11e-4089-9a3b-77294a85c2c5",
                "room_type_id": "877d2bd2-74a0-4d77-ad1c-a69ae0cee94d",
            },
            {
                "booked": 10,
                "date": "2023-09-02",
                "rate_plan_id": "dd1e2ead-b503-4289-a57e-ad51184fafbe",
                "room_type_id": "877d2bd2-74a0-4d77-ad1c-a69ae0cee94d",
            },
            {
                "booked": 10,
                "date": "2023-09-02",
                "rate_plan_id": "3285e794-c11e-4089-9a3b-77294a85c2c5",
                "room_type_id": "877d2bd2-74a0-4d77-ad1c-a69ae0cee94d",
            },
        ]
        room_type = RoomType.objects.filter(hotel=hotel).first()

        (
            restriction_update_to_channex,
            restriction_create_to_db,
        ) = adapter._get_restrictions_to_update(
            room_type_uuid=room_type.uuid,
            room_type_pms_id=room_type.pms_id,
            sorted_date_range=adapter._get_date_range(payload),
        )
        assert restriction_update_to_channex == [
            {
                "date": "2023-09-01",
                "rate_plan_id": "3285e794-c11e-4089-9a3b-77294a85c2c5",
                "property_id": hotel.pms_id,
                "rate": 700000,
            },
            {
                "date": "2023-09-02",
                "rate_plan_id": "3285e794-c11e-4089-9a3b-77294a85c2c5",
                "property_id": hotel.pms_id,
                "rate": 750000,
            },
            {
                "date": "2023-09-01",
                "rate_plan_id": "dd1e2ead-b503-4289-a57e-ad51184fafbe",
                "property_id": hotel.pms_id,
                "rate": 800000,
            },
            {
                "date": "2023-09-02",
                "rate_plan_id": "dd1e2ead-b503-4289-a57e-ad51184fafbe",
                "property_id": hotel.pms_id,
                "rate": 850000,
            },
        ]
        assert len(restriction_create_to_db) == 2

    def test_handle_booked_ari_trigger(
        self,
        mocked_channex_validation,
        mocker,
        hotel_factory,
        rate_plan_factory,
        room_type_factory,
    ):
        hotel = hotel_factory(channex=True)
        room_type = room_type_factory(hotel=hotel)
        rate_plan = rate_plan_factory(room_type=room_type)
        adapter = ChannexPMSAdapter(hotel)
        mocker.patch(
            "backend.pms.adapter.channex.ChannexPMSAdapter._get_restrictions_to_update",
            return_value=(
                [{}],
                [
                    RatePlanRestrictions(
                        rate_plan=rate_plan,
                        date=timezone.localtime().date(),
                        rate=100000,
                    )
                ],
            ),
        )
        mocker.patch(
            "backend.utils.channex_client.ChannexClient.update_room_type_rate_plan_restrictions",
            return_value=mocker.Mock(status_code=200),
        )
        adapter.handle_booked_ari_trigger(
            room_type_uuid=uuid.uuid4(),
            payload=[],
        )
        mocker.patch(
            "backend.utils.channex_client.ChannexClient.update_room_type_rate_plan_restrictions",
            return_value=mocker.Mock(status_code=401),
        )

        adapter.handle_booked_ari_trigger(room_type_uuid=uuid.uuid4(), payload=[])

        adapter = ChannexPMSAdapter(hotel)
        hotel.inventory_days = 500
        hotel.save()
        mocker.patch(
            "django.utils.timezone.localtime",
            return_value=timezone.datetime(
                2023,
                4,
                24,
                0,
                30,
                54,
                645056,
                tzinfo=zoneinfo.ZoneInfo(key="Asia/Ho_Chi_Minh"),
            ),
        )
        last_date = timezone.datetime(
            2024,
            9,
            4,
            0,
            31,
            21,
            146832,
            tzinfo=zoneinfo.ZoneInfo(key="Asia/Ho_Chi_Minh"),
        )
        adapter.handle_booked_ari_trigger(
            room_type_uuid=uuid.uuid4(),
            payload=[{"date": last_date.strftime("%Y-%m-%d")}],
        )

    def test_handle_time_based_trigger(
        self,
        mocker,
        mocked_channex_validation,
        hotel_factory,
        room_type_factory,
        rate_plan_factory,
    ):
        hotel = hotel_factory(channex=True)
        room_type = room_type_factory(hotel=hotel)
        rate_plan = rate_plan_factory(room_type=room_type)
        adapter = ChannexPMSAdapter(hotel)
        mocker.patch(
            "backend.pms.adapter.channex.ChannexPMSAdapter._get_restrictions_to_update",
            return_value=([], []),
        )
        adapter.handle_time_based_trigger(date=timezone.localtime().date())
        mocker_get_restrictions = mocker.patch(
            "backend.pms.adapter.channex.ChannexPMSAdapter._get_restrictions_to_update",
            return_value=(
                [{}],
                [
                    RatePlanRestrictions(
                        rate_plan=rate_plan,
                        date=timezone.localtime().date(),
                        rate=100000,
                    )
                ],
            ),
        )
        mocker_update_room = mocker.patch(
            "backend.utils.channex_client.ChannexClient.update_room_type_rate_plan_restrictions",
            return_value=mocker.Mock(status_code=200),
        )
        adapter.handle_time_based_trigger(date=timezone.localtime().date())
        mocker_get_restrictions.assert_called_once()
        mocker_update_room.assert_called_once()
        assert RatePlanRestrictions.objects.filter(
            rate_plan=rate_plan,
            date=timezone.localtime().date(),
            rate=100000,
        ).exists()
