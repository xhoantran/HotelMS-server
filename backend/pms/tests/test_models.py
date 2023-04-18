import pytest
from django.contrib.auth import get_user_model

from ..adapter import ChannexPMSAdapter, DefaultPMSAdapter
from ..models import Hotel, HotelEmployee

User = get_user_model()


class TestHotelModel:
    def test_default_setting(self, hotel_factory):
        hotel = hotel_factory()
        assert hotel.pms == Hotel.PMSChoices.__empty__
        assert isinstance(hotel.adapter, DefaultPMSAdapter)

    def test_validation(self, mocker, hotel_factory):
        hotel = hotel_factory()
        hotel.inventory_days = 99
        with pytest.raises(ValueError):
            hotel.save()

        hotel = hotel_factory()
        hotel.pms = Hotel.PMSChoices.CHANNEX
        with pytest.raises(ValueError):
            hotel.save()

        mocker.patch(
            "backend.utils.channex_client.ChannexClient.get_properties",
            return_value=mocker.Mock(status_code=404),
        )
        hotel.external_api_key = "test"
        hotel.external_id = "test"
        with pytest.raises(ValueError):
            hotel.save()

        mocker.patch(
            "backend.utils.channex_client.ChannexClient.get_properties",
            return_value=mocker.Mock(status_code=200),
        )
        mocker.patch(
            "backend.utils.channex_client.ChannexClient.get_property",
            return_value=mocker.Mock(status_code=404),
        )
        with pytest.raises(ValueError):
            hotel.save()

    def test_invalid_pms(self, hotel_factory):
        hotel = hotel_factory()
        hotel.pms = "invalid"
        with pytest.raises(ValueError):
            hotel.adapter

    def test_channex(self, mocker, hotel_factory):
        mocker.patch(
            "backend.utils.channex_client.requests.get",
            return_value=mocker.Mock(status_code=200),
        )
        hotel = hotel_factory(channex=True)
        assert isinstance(hotel.adapter, ChannexPMSAdapter)


def test_hotel_employee_model(db):
    user = User.objects.create(
        username="test",
        email="test",
        name="test",
        role=User.UserRoleChoices.ADMIN,
    )
    with pytest.raises(ValueError):
        HotelEmployee.objects.create(
            user=user,
            hotel=None,
        )
