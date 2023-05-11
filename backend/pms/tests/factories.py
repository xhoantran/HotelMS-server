from django.contrib.auth import get_user_model
from factory import Faker, Sequence, SubFactory
from factory.django import DjangoModelFactory

from ..models import Hotel, HotelEmployee, RatePlan, Room, RoomType

User = get_user_model()


class HotelFactory(DjangoModelFactory):
    name = Faker("company")
    inventory_days = Faker("pyint", min_value=100, max_value=700)

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

    class Meta:
        model = RoomType


class RatePlanFactory(DjangoModelFactory):
    name = Faker("word")
    room_type = SubFactory(RoomTypeFactory)

    class Meta:
        model = RatePlan


class RoomFactory(DjangoModelFactory):
    number = Sequence(int)
    room_type = SubFactory(RoomTypeFactory)

    class Meta:
        model = Room
