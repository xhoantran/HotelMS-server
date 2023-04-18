import pytest
from django.utils import timezone

from ..adapter import (
    ChannexPMSAdapter,
    DefaultPMSAdapter,
    PMSBaseAdapter,
    RoomTypeAdapter,
)


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
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=20),
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

    assert adapter._convert_to_id(hotel.id, type(hotel)) == hotel.id

    with pytest.raises(TypeError):
        adapter._convert_to_id(object(), type(hotel))

    with pytest.raises(TypeError):
        PMSBaseAdapter(hotel=object())

    with pytest.raises(NotImplementedError):
        adapter.get_rate_plans()

    with pytest.raises(NotImplementedError):
        adapter.get_room_types()

    with pytest.raises(NotImplementedError):
        adapter.get_room_type_rate_plan_restrictions()


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

    def test_get_room_type_rate_plan_restrictions(
        self,
        hotel_factory,
        room_type_factory,
        rate_plan_factory,
    ):
        hotel = hotel_factory()
        room_type = room_type_factory(hotel=hotel)
        rate_plan_factory(room_type=room_type)
        adapter = DefaultPMSAdapter(hotel)
        assert (
            adapter.get_room_type_rate_plan_restrictions(
                room_type=room_type, date=timezone.now()
            ).count()
            == 1
        )
        assert (
            adapter.get_room_type_rate_plan_restrictions(
                room_type=room_type.id,
                date_from=timezone.now(),
                date_to=timezone.now() + timezone.timedelta(days=20),
            ).count()
            == 21
        )
        with pytest.raises(ValueError):
            adapter.get_room_type_rate_plan_restrictions(room_type=room_type.id)


class TestChannexPMSAdapter:
    def test_init(
        self,
        mocked_channex_validation,
        mocker,
        hotel_factory,
    ):
        hotel = hotel_factory(channex=True)
        adapter = ChannexPMSAdapter(hotel)
        assert adapter.hotel == hotel

    # def test_get_room_type_rate_plan_restrictions(
    #     self,
    #     mocked_channex_validation,
    #     mocker,
    #     hotel_factory,
    #     room_type_factory,
    # ):
    #     hotel = hotel_factory(channex=True)
    #     room_type = room_type_factory(hotel=hotel)
    #     adapter = ChannexPMSAdapter(hotel)
    #     mocker.patch(
    #         "backend.utils.channex_client.ChannexClient.get_room_type_rate_plan_restrictions",
    #         return_value=mocker.Mock(
    #             status_code=200,
    #             json=mocker.Mock(
    #                 return_value={
    #                     "data": {
    #                         "0c9a0fba-71f3-4da4-af98-f9f036923dd8": {
    #                             "2023-04-17": {"rate": "1000000"},
    #                         },
    #                         "90b1373c-dcf0-46be-a440-d7ac525967a3": {
    #                             "2023-04-17": {"rate": "1000000"},
    #                         },
    #                         "dd1e2ead-b503-4289-a57e-ad51184fafbe": {
    #                             "2023-04-17": {"rate": "0"},
    #                         },
    #                     }
    #                 }
    #             ),
    #         ),
    #     )
    #     assert (
    #         adapter.get_room_type_rate_plan_restrictions(
    #             room_type=room_type, date=timezone.now()
    #         ).count()
    #         == 3
    #     )
