import pytest
from django.contrib.sites.models import Site
from rest_framework.test import APIClient, RequestsClient
from rest_framework_simplejwt.tokens import RefreshToken

from backend.cm.app_settings import CM_API_KEY_HEADER
from backend.cm.tests.factories import PropertyFactory
from backend.pms.tests.factories import (
    BookingFactory,
    HotelFactory,
    RatePlanFactory,
    RatePlanRestrictionsFactory,
    RoomFactory,
    RoomTypeFactory,
)
from backend.rms.adapter import DynamicPricingAdapter
from backend.rms.tests.factories import (
    AvailabilityBasedTriggerRuleFactory,
    DynamicPricingSettingFactory,
    LeadDaysBasedRuleFactory,
    MonthBasedRuleFactory,
    SeasonBasedRuleFactory,
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
def get_callback_client():
    def callback_client(api_key):
        client = RequestsClient()
        client.headers.update({CM_API_KEY_HEADER: api_key})
        return client

    return callback_client


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
def dynamic_pricing_adapter_factory(db) -> DynamicPricingAdapter:
    return DynamicPricingAdapter


@pytest.fixture
def dynamic_pricing_setting_factory(db) -> DynamicPricingSettingFactory:
    return DynamicPricingSettingFactory


@pytest.fixture
def weekday_based_rule_factory(db):
    return WeekdayBasedRuleFactory


@pytest.fixture
def month_based_rule_factory(db):
    return MonthBasedRuleFactory


@pytest.fixture
def season_based_rule_factory(db):
    return SeasonBasedRuleFactory


@pytest.fixture
def lead_days_based_rule_factory(db):
    return LeadDaysBasedRuleFactory


@pytest.fixture
def availability_based_rule_factory(db):
    return AvailabilityBasedTriggerRuleFactory


@pytest.fixture
def property_factory(db) -> PropertyFactory:
    return PropertyFactory
