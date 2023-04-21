from django.contrib.auth import get_user_model
from django.utils import timezone
from factory import Faker, Sequence, SubFactory, Trait, lazy_attribute
from factory.django import DjangoModelFactory

from ..models import (
    Booking,
    Hotel,
    HotelEmployee,
    HotelGroup,
    RatePlan,
    RatePlanRestrictions,
    Room,
    RoomType,
)

User = get_user_model()


class HotelGroupFactory(DjangoModelFactory):
    name = Faker("word")

    class Meta:
        model = HotelGroup
        django_get_or_create = ("name",)


class HotelFactory(DjangoModelFactory):
    name = Faker("company")
    inventory_days = Faker("pyint", min_value=100, max_value=700)
    group = SubFactory(HotelGroupFactory)

    class Params:
        channex = Trait(
            pms=Hotel.PMSChoices.CHANNEX,
            pms_id=Faker("uuid4"),
            pms_api_key=Faker("password", length=32, special_chars=False),
        )

    class Meta:
        model = Hotel


class HotelEmployeeFactory(DjangoModelFactory):
    user = SubFactory(
        "backend.users.tests.factories.UserFactory",
        role=User.UserRoleChoices.MANAGER,
        hotel_employee=None,
    )
    hotel = SubFactory(HotelFactory)

    class Meta:
        model = HotelEmployee


class RoomTypeFactory(DjangoModelFactory):
    hotel = SubFactory(HotelFactory)
    name = Faker("word")
    number_of_beds = Faker("pyint", min_value=1, max_value=10)
    base_rate = Faker("pydecimal", left_digits=2, right_digits=2, positive=True)
    pms_id = Faker("uuid4")

    class Meta:
        model = RoomType


class RatePlanFactory(DjangoModelFactory):
    name = Faker("word")
    room_type = SubFactory(RoomTypeFactory)
    pms_id = Faker("uuid4")

    class Meta:
        model = RatePlan


class RatePlanRestrictionsFactory(DjangoModelFactory):
    rate_plan = SubFactory(RatePlanFactory)
    date = Sequence(lambda n: timezone.now().date() + timezone.timedelta(days=n))
    rate = Faker("pydecimal", left_digits=2, right_digits=2, positive=True)

    class Meta:
        model = RatePlanRestrictions


class RoomFactory(DjangoModelFactory):
    number = Sequence(int)
    room_type = SubFactory(RoomTypeFactory)

    class Meta:
        model = Room


class BookingFactory(DjangoModelFactory):
    user = SubFactory(
        "backend.users.tests.factories.UserFactory",
        role=User.UserRoleChoices.GUEST,
    )
    room = SubFactory(RoomFactory)
    rate = Faker("pydecimal", left_digits=2, right_digits=2, positive=True)
    start_date = Sequence(lambda n: timezone.now().date() + timezone.timedelta(days=n))

    @lazy_attribute
    def end_date(self):
        ret = self.start_date + timezone.timedelta(days=self.duration)
        BookingFactory.reset_sequence((ret - timezone.now().date()).days)
        return ret

    class Params:
        duration = Faker("pyint", min_value=1, max_value=10)

    class Meta:
        model = Booking
