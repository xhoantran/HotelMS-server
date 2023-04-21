import pytest
from django.contrib.sites.models import Site
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from backend.pms.tests.factories import (
    BookingFactory,
    HotelFactory,
    HotelGroupFactory,
    RatePlanFactory,
    RatePlanRestrictionsFactory,
    RoomFactory,
    RoomTypeFactory,
)
from backend.rms.tests.factories import (
    AvailabilityBasedTriggerRuleFactory,
    DynamicPricingSettingFactory,
    LeadDaysBasedRuleFactory,
    MonthBasedRuleFactory,
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
def current_site(db):
    return Site.objects.get_current()


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
def rate_plan_restrictions_factory(db) -> RatePlanRestrictionsFactory:
    return RatePlanRestrictionsFactory


@pytest.fixture
def room_factory(db) -> RoomFactory:
    return RoomFactory


@pytest.fixture
def booking_factory(db) -> BookingFactory:
    return BookingFactory


@pytest.fixture
def mocked_channex_validation(mocker):
    mocker.patch(
        "backend.pms.adapter.channex.ChannexPMSAdapter.validate_api_key",
        return_value=True,
    )
    mocker.patch(
        "backend.utils.channex_client.ChannexClient.get_property",
        return_value=mocker.Mock(
            status_code=200,
            json=mocker.Mock(
                # Removed unnecessary fields
                return_value={
                    "data": {
                        "attributes": {
                            "settings": {"state_length": 200},
                        }
                    }
                }
            ),
        ),
    )
    mocker.patch(
        "backend.utils.channex_client.ChannexClient.get_rate_plans",
        return_value=mocker.Mock(
            status_code=200,
            json=mocker.Mock(
                # Removed unnecessary fields
                return_value={"data": []}
            ),
        ),
    )
    mocker.patch(
        "backend.utils.channex_client.ChannexClient.create_webhook",
        return_value=mocker.Mock(status_code=201),
    )


@pytest.fixture
def hotel_group_factory(db) -> HotelGroupFactory:
    return HotelGroupFactory


@pytest.fixture
def dynamic_pricing_setting_factory(db) -> DynamicPricingSettingFactory:
    return DynamicPricingSettingFactory


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
def availability_based_rule_factory(db) -> AvailabilityBasedTriggerRuleFactory:
    return AvailabilityBasedTriggerRuleFactory


@pytest.fixture
def time_based_rule_factory(db) -> TimeBasedTriggerRuleFactory:
    return TimeBasedTriggerRuleFactory
