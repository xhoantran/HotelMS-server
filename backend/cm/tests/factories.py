from factory import Faker, SubFactory, Trait
from factory.django import DjangoModelFactory

from backend.pms.tests.factories import HotelFactory, RatePlanFactory, RoomTypeFactory

from ..models import CMHotel, CMRatePlan, CMRoomType, HotelAPIKey


class CMHotelFactory(DjangoModelFactory):
    hotel = SubFactory(HotelFactory)

    class Params:
        channex = Trait(
            cm=CMHotel.CMChoices.CHANNEX,
            cm_id=Faker("uuid4"),
            cm_api_key=Faker("password", length=32, special_chars=False),
        )

    class Meta:
        model = CMHotel


class CMRoomTypeFactory(DjangoModelFactory):
    room_type = SubFactory(RoomTypeFactory)
    cm_id = Faker("uuid4")

    class Meta:
        model = CMRoomType


class CMRatePlanFactory(DjangoModelFactory):
    rate_plan = SubFactory(RatePlanFactory)
    cm_id = Faker("uuid4")

    class Meta:
        model = CMRatePlan
