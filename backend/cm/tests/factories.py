from factory import Faker, SubFactory, Trait
from factory.django import DjangoModelFactory

from backend.pms.tests.factories import HotelFactory, RatePlanFactory, RoomTypeFactory

from ..models import CMHotelConnector, CMRatePlanConnector, CMRoomTypeConnector


class CMHotelConnectorFactory(DjangoModelFactory):
    pms = SubFactory(HotelFactory)

    class Params:
        channex = Trait(
            channel_manager=CMHotelConnector.ChannelManagerChoices.CHANNEX,
            cm_id=Faker("uuid4"),
            cm_api_key=Faker("password", length=32, special_chars=False),
        )

    class Meta:
        model = CMHotelConnector


class CMRoomTypeConnectorFactory(DjangoModelFactory):
    pms = SubFactory(RoomTypeFactory)
    cm_name = Faker("word")
    cm_id = Faker("uuid4")

    class Meta:
        model = CMRoomTypeConnector


class CMRatePlanConnectorFactory(DjangoModelFactory):
    pms = SubFactory(RatePlanFactory)
    cm_name = Faker("word")
    cm_id = Faker("uuid4")

    class Meta:
        model = CMRatePlanConnector
