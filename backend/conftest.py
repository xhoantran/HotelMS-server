import uuid

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from backend.cm.tests.factories import (
    CMHotelConnectorFactory,
    CMRatePlanConnectorFactory,
    CMRoomTypeConnectorFactory,
)
from backend.pms.models import Booking
from backend.pms.tests.factories import (
    HotelFactory,
    RatePlanFactory,
    RoomFactory,
    RoomTypeFactory,
)
from backend.rms.tests.factories import (
    DynamicPricingSettingFactory,
    IntervalBaseRateFactory,
    LeadDaysBasedRuleFactory,
    MonthBasedRuleFactory,
    OccupancyBasedTriggerRuleFactory,
    SeasonBasedRuleFactory,
    TimeBasedTriggerRuleFactory,
    WeekdayBasedRuleFactory,
)
from backend.users.models import User
from backend.users.tests.factories import SuperAdminFactory, UserFactory


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def super_admin(db) -> User:
    return SuperAdminFactory()


@pytest.fixture
def user(db) -> User:
    return UserFactory()


@pytest.fixture
def admin(db) -> User:
    return UserFactory(role=User.UserRoleChoices.ADMIN)


@pytest.fixture
def manager(db) -> User:
    return UserFactory(role=User.UserRoleChoices.MANAGER)


@pytest.fixture
def receptionist(db) -> User:
    return UserFactory(role=User.UserRoleChoices.RECEPTIONIST)


@pytest.fixture
def staff(db) -> User:
    return UserFactory(role=User.UserRoleChoices.STAFF)


@pytest.fixture
def guest(db) -> User:
    return UserFactory(role=User.UserRoleChoices.GUEST)


@pytest.fixture
def get_api_client():
    def api_client(user):
        client = APIClient()
        refresh = RefreshToken.for_user(user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        return client

    return api_client


@pytest.fixture
def hotel_factory(db) -> HotelFactory:
    return HotelFactory


@pytest.fixture
def room_type_factory(db) -> RoomTypeFactory:
    return RoomTypeFactory


@pytest.fixture
def rate_plan_factory(db) -> RatePlanFactory:
    return RatePlanFactory


@pytest.fixture
def room_factory(db) -> RoomFactory:
    return RoomFactory


@pytest.fixture
def dynamic_pricing_setting_factory(db) -> DynamicPricingSettingFactory:
    return DynamicPricingSettingFactory


@pytest.fixture
def interval_base_rate_factory(db) -> IntervalBaseRateFactory:
    return IntervalBaseRateFactory


@pytest.fixture
def weekday_based_rule_factory(db) -> WeekdayBasedRuleFactory:
    return WeekdayBasedRuleFactory


@pytest.fixture
def month_based_rule_factory(db) -> MonthBasedRuleFactory:
    return MonthBasedRuleFactory


@pytest.fixture
def season_based_rule_factory(db) -> SeasonBasedRuleFactory:
    return SeasonBasedRuleFactory


@pytest.fixture
def lead_days_based_rule_factory(db) -> LeadDaysBasedRuleFactory:
    return LeadDaysBasedRuleFactory


@pytest.fixture
def occupancy_based_rule_factory(db) -> OccupancyBasedTriggerRuleFactory:
    return OccupancyBasedTriggerRuleFactory


@pytest.fixture
def time_based_rule_factory(db) -> TimeBasedTriggerRuleFactory:
    return TimeBasedTriggerRuleFactory


@pytest.fixture
def cm_hotel_connector_factory(db) -> CMHotelConnectorFactory:
    return CMHotelConnectorFactory


@pytest.fixture
def cm_room_type_connector_factory(db) -> CMRoomTypeConnectorFactory:
    return CMRoomTypeConnectorFactory


@pytest.fixture
def cm_rate_plan_connector_factory(db) -> CMRatePlanConnectorFactory:
    return CMRatePlanConnectorFactory


@pytest.fixture
def mocked_channex_validation(mocker):
    mocker.patch(
        "backend.cm.client.channex.ChannexClient.list_properties",
        return_value=[],
    )
    mocker.patch(
        "backend.cm.client.channex.ChannexClient.get_property",
        return_value={
            "attributes": {
                "title": "Hotel Title",
                "address": "Address",
                "city": "City",
                "country": "VN",
                # We use VND because of its fractional unit is 1
                "currency": "VND",
                "timezone": "Asia/Ho_Chi_Minh",
                "settings": {"state_length": 200},
            },
            "id": str(uuid.uuid4()),
        },
    )
    mocker.patch(
        "backend.cm.client.channex.ChannexClient.list_room_types",
        return_value=[],
    )
    mocker.patch(
        "backend.cm.client.channex.ChannexClient.list_rate_plans",
        return_value=[],
    )
    mocker.patch(
        "backend.cm.client.channex.ChannexClient.update_or_create_webhook",
        return_value=mocker.Mock(status_code=201),
    )


@pytest.fixture
def mocked_channex_setup_hotel(mocker):
    hotel_id = str(uuid.uuid4())
    rate_plan_1_id = str(uuid.uuid4())
    rate_plan_2_id = str(uuid.uuid4())
    room_type_1_id = str(uuid.uuid4())
    room_type_2_id = str(uuid.uuid4())

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
    mocker.patch(
        "backend.cm.client.channex.ChannexClient.list_bookings",
        side_effect=[
            [
                {
                    "attributes": {
                        "status": Booking.StatusChoices.NEW,
                        "arrival_date": "2020-01-01",
                        "departure_date": "2020-01-03",
                        "rooms": [
                            {
                                "checkin_date": "2020-01-01",
                                "checkout_date": "2020-01-03",
                                "room_type_id": room_type_1_id,
                            },
                        ],
                    },
                    "id": str(uuid.uuid4()),
                }
            ],
            [],
        ],
    )

    return {
        "hotel_id": hotel_id,
        "rate_plan_1_id": rate_plan_1_id,
        "rate_plan_2_id": rate_plan_2_id,
        "room_type_1_id": room_type_1_id,
        "room_type_2_id": room_type_2_id,
    }
