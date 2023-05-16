import datetime
import uuid

import pytest

from backend.pms.models import Booking, Hotel, RatePlan, RatePlanRestrictions, RoomType

from ..adapter import ChannexAdapter, ChannexException
from ..client.channex import ChannexClientAPIError
from ..models import CMHotelConnector, CMRatePlanConnector, CMRoomTypeConnector


def test_validate_api_key(mocker):
    mocker.patch(
        "backend.cm.client.channex.ChannexClient._get",
        return_value=mocker.Mock(
            status_code=401,
        ),
    )
    assert not ChannexAdapter.validate_api_key("invalid_api_key")


def test_validate_property_id(mocker):
    mocker.patch(
        "backend.cm.client.channex.ChannexClient._get",
        return_value=mocker.Mock(
            status_code=404,
        ),
    )
    assert not ChannexAdapter.validate_property_id(
        "valid_api_key", "invalid_property_id"
    )


def test_serialize_property_structure(db, mocked_channex_validation, mocker):
    cm_hotel_connector = CMHotelConnector(
        channel_manager=CMHotelConnector.ChannelManagerChoices.CHANNEX,
        cm_id="hotel_id",
        cm_api_key="valid_api_key",
    )

    # Error
    mocker.patch(
        "backend.cm.client.channex.ChannexClient.list_rate_plans",
        side_effect=ChannexClientAPIError("error"),
    )
    with pytest.raises(ChannexException):
        cm_hotel_connector.adapter.serialize_property_structure()

    # Success case
    hotel_id = str(uuid.uuid4())
    rate_plan_1_id = str(uuid.uuid4())
    rate_plan_2_id = str(uuid.uuid4())
    room_type_1_id = str(uuid.uuid4())
    room_type_2_id = str(uuid.uuid4())

    cm_hotel_connector = CMHotelConnector(
        channel_manager=CMHotelConnector.ChannelManagerChoices.CHANNEX,
        cm_id=hotel_id,
        cm_api_key="valid_api_key",
    )

    mocker.patch(
        "backend.cm.client.channex.ChannexClient.list_rate_plans",
        return_value=[
            {
                "attributes": {
                    "title": "rate_plan_1",
                    "room_type_id": room_type_1_id,
                },
                "id": rate_plan_1_id,
            },
            {
                "attributes": {
                    "title": "rate_plan_2",
                    "room_type_id": room_type_2_id,
                },
                "id": rate_plan_2_id,
            },
        ],
    )
    mocker.patch(
        "backend.cm.client.channex.ChannexClient.list_room_types",
        return_value=[
            {
                "attributes": {
                    "title": "room_type_1",
                },
                "id": room_type_1_id,
            },
            {
                "attributes": {
                    "title": "room_type_2",
                },
                "id": room_type_2_id,
            },
        ],
    )
    mocker.patch(
        "backend.cm.client.channex.ChannexClient.get_property",
        return_value={
            "attributes": {
                "title": "hotel",
                "address": "address",
                "city": "city",
                "country": "VN",
                "currency": "VND",
                "timezone": "Asia/Ho_Chi_Minh",
                "settings": {
                    "state_length": 500,
                },
            },
            "id": hotel_id,
        },
    )
    assert cm_hotel_connector.adapter.serialize_property_structure().data == {
        "cm_id": hotel_id,
        "cm_name": "hotel",
        "pms": {
            "name": "hotel",
            "address": "address",
            "city": "city",
            "country": "VN",
            "currency": "VND",
            "timezone": "Asia/Ho_Chi_Minh",
            "inventory_days": 500,
        },
        "cm_room_type_connectors": [
            {
                "cm_id": room_type_1_id,
                "cm_name": "room_type_1",
                "cm_rate_plan_connectors": [
                    {
                        "cm_id": rate_plan_1_id,
                        "cm_name": "rate_plan_1",
                    },
                ],
            },
            {
                "cm_id": room_type_2_id,
                "cm_name": "room_type_2",
                "cm_rate_plan_connectors": [
                    {
                        "cm_id": rate_plan_2_id,
                        "cm_name": "rate_plan_2",
                    },
                ],
            },
        ],
    }
    cm_hotel_connector.adapter.save_serialize_property_structure(
        serializer=cm_hotel_connector.adapter.serialize_property_structure(),
        cm_api_key="valid_api_key",
    )
    assert Hotel.objects.count() == 1
    assert RatePlan.objects.count() == 2
    assert RoomType.objects.count() == 2
    assert CMHotelConnector.objects.count() == 1
    assert CMRatePlanConnector.objects.count() == 2
    assert CMRoomTypeConnector.objects.count() == 2

    room_type_1_pms_id = CMRoomTypeConnector.objects.get(cm_id=room_type_1_id).pms.id
    room_type_2_pms_id = CMRoomTypeConnector.objects.get(cm_id=room_type_2_id).pms.id
    rate_plan_1_pms_id = CMRatePlanConnector.objects.get(cm_id=rate_plan_1_id).pms.id
    rate_plan_2_pms_id = CMRatePlanConnector.objects.get(cm_id=rate_plan_2_id).pms.id
    # test_get_room_type_id_map
    assert CMHotelConnector.objects.first().adapter.get_room_type_id_map() == {
        "cm": {
            "None": None,  # Unmapped room type
            room_type_1_id: room_type_1_pms_id,
            room_type_2_id: room_type_2_pms_id,
        },
        "pms": {
            "None": None,  # Unmapped room type
            room_type_1_pms_id: room_type_1_id,
            room_type_2_pms_id: room_type_2_id,
        },
    }

    # test_get_rate_plan_id_map
    assert CMHotelConnector.objects.first().adapter.get_rate_plan_id_map() == {
        "cm": {
            "None": None,  # Unmapped rate plan
            rate_plan_1_id: rate_plan_1_pms_id,
            rate_plan_2_id: rate_plan_2_pms_id,
        },
        "pms": {
            "None": None,  # Unmapped rate plan
            rate_plan_1_pms_id: rate_plan_1_id,
            rate_plan_2_pms_id: rate_plan_2_id,
        },
    }


def test_get_all_upcoming_bookings(
    mocked_channex_validation, mocker, cm_hotel_connector_factory
):
    mocker.patch(
        "backend.cm.client.channex.ChannexClient.list_bookings",
        side_effect=[[1, 2, 3], [4, 5, 6], []],
    )
    cm_hotel_connector: CMHotelConnector = cm_hotel_connector_factory(channex=True)
    all_upcoming_booking = cm_hotel_connector.adapter.get_all_upcoming_bookings(limit=3)
    assert all_upcoming_booking == [1, 2, 3, 4, 5, 6]

    mocker.patch(
        "backend.cm.client.channex.ChannexClient.list_bookings",
        side_effect=ChannexClientAPIError("error"),
    )
    with pytest.raises(ChannexException):
        cm_hotel_connector.adapter.get_all_upcoming_bookings(limit=3)


def test_save_all_upcoming_bookings(
    mocked_channex_validation, mocker, cm_hotel_connector_factory
):
    hotel_id = str(uuid.uuid4())
    rate_plan_id = str(uuid.uuid4())
    room_type_id = str(uuid.uuid4())
    cm_hotel_connector = CMHotelConnector(
        channel_manager=CMHotelConnector.ChannelManagerChoices.CHANNEX,
        cm_id=hotel_id,
        cm_api_key="valid_api_key",
    )

    mocker.patch(
        "backend.cm.client.channex.ChannexClient.list_rate_plans",
        return_value=[
            {
                "attributes": {
                    "title": "rate_plan_1",
                    "room_type_id": room_type_id,
                },
                "id": rate_plan_id,
            }
        ],
    )
    mocker.patch(
        "backend.cm.client.channex.ChannexClient.list_room_types",
        return_value=[
            {
                "attributes": {
                    "title": "room_type_1",
                },
                "id": room_type_id,
            },
        ],
    )
    mocker.patch(
        "backend.cm.client.channex.ChannexClient.get_property",
        return_value={
            "attributes": {
                "title": "hotel",
                "address": "address",
                "city": "city",
                "country": "VN",
                "currency": "VND",
                "timezone": "Asia/Ho_Chi_Minh",
                "settings": {
                    "state_length": 500,
                },
            },
            "id": hotel_id,
        },
    )
    cm_hotel_connector.adapter.save_serialize_property_structure(
        serializer=cm_hotel_connector.adapter.serialize_property_structure(),
        cm_api_key="valid_api_key",
    )
    assert RoomType.objects.count() == 1

    mocker.patch(
        "backend.cm.client.channex.ChannexClient.list_bookings",
        side_effect=[
            [
                {
                    "attributes": {
                        "status": Booking.StatusChoices.NEW,
                        "arrival_date": "2020-01-01",
                        "departure_date": "2020-01-03",
                        "inserted_at": "2020-01-01T00:00:00+00:00",
                        "rooms": [
                            {
                                "checkin_date": "2020-01-01",
                                "checkout_date": "2020-01-03",
                                "room_type_id": room_type_id,
                            },
                        ],
                    },
                    "id": str(uuid.uuid4()),
                }
            ],
            [],
        ],
    )
    cm_hotel_connector = CMHotelConnector.objects.get(
        channel_manager=CMHotelConnector.ChannelManagerChoices.CHANNEX,
        cm_id=hotel_id,
    )
    cm_hotel_connector.adapter.save_all_upcoming_bookings()

    new_booking = Booking.objects.first()
    assert new_booking.status == Booking.StatusChoices.NEW
    assert new_booking.dates.lower == datetime.date(2020, 1, 1)
    assert new_booking.dates.upper == datetime.date(2020, 1, 3)
    assert new_booking.booking_rooms.count() == 1

    new_booking_room = new_booking.booking_rooms.first()
    assert new_booking_room.room_type == RoomType.objects.first()
    assert new_booking_room.dates.lower == datetime.date(2020, 1, 1)
    assert new_booking_room.dates.upper == datetime.date(2020, 1, 3)


def test_get_prep_rate_plan_restrictions(db, mocked_channex_validation, mocker):
    hotel_id = str(uuid.uuid4())
    rate_plan_id = str(uuid.uuid4())
    room_type_id = str(uuid.uuid4())
    cm_hotel_connector = CMHotelConnector(
        channel_manager=CMHotelConnector.ChannelManagerChoices.CHANNEX,
        cm_id=hotel_id,
        cm_api_key="valid_api_key",
    )

    mocker.patch(
        "backend.cm.client.channex.ChannexClient.list_rate_plans",
        return_value=[
            {
                "attributes": {
                    "title": "rate_plan_1",
                    "room_type_id": room_type_id,
                },
                "id": rate_plan_id,
            }
        ],
    )
    mocker.patch(
        "backend.cm.client.channex.ChannexClient.list_room_types",
        return_value=[
            {
                "attributes": {
                    "title": "room_type_1",
                },
                "id": room_type_id,
            },
        ],
    )
    mocker.patch(
        "backend.cm.client.channex.ChannexClient.get_property",
        return_value={
            "attributes": {
                "title": "hotel",
                "address": "address",
                "city": "city",
                "country": "VN",
                "currency": "VND",
                "timezone": "Asia/Ho_Chi_Minh",
                "settings": {
                    "state_length": 500,
                },
            },
            "id": hotel_id,
        },
    )
    cm_hotel_connector.adapter.save_serialize_property_structure(
        serializer=cm_hotel_connector.adapter.serialize_property_structure(),
        cm_api_key="valid_api_key",
    )

    assert Hotel.objects.count() == 1
    assert RoomType.objects.count() == 1
    assert RatePlan.objects.count() == 1

    cm_hotel_connector = CMHotelConnector.objects.get(
        channel_manager=CMHotelConnector.ChannelManagerChoices.CHANNEX,
        cm_id=hotel_id,
    )

    assert cm_hotel_connector.adapter.get_prep_rate_plan_restrictions(
        new_rate_plan_restrictions=[
            RatePlanRestrictions(
                rate_plan=CMRatePlanConnector.objects.get(cm_id=rate_plan_id).pms,
                date=datetime.date(2020, 1, 1),
                rate=100,
            )
        ]
    ) == [
        {
            "property_id": hotel_id,
            "rate_plan_id": rate_plan_id,
            "date": "2020-01-01",
            "rate": 100,
        }
    ]

    # save_rate_plan_restrictions
    mocker.patch(
        "backend.cm.client.channex.ChannexClient.update_rate_plan_restrictions",
        return_value=mocker.Mock(
            status_code=200,
        ),
    )
    cm_hotel_connector.adapter.save_rate_plan_restrictions(
        new_rate_plan_restrictions=[
            RatePlanRestrictions(
                rate_plan=CMRatePlanConnector.objects.get(cm_id=rate_plan_id).pms,
                date=datetime.date(2020, 1, 1),
                rate=100,
            )
        ]
    )
