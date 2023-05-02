import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from ..adapter import ChannexPMSAdapter, DefaultPMSAdapter
from ..models import Hotel, HotelEmployee

User = get_user_model()


class TestHotelModel:
    def test_default_setting(self, hotel_factory):
        hotel = hotel_factory(name="Hotel")
        assert str(hotel) == "Hotel"
        assert hotel.pms == ""
        assert isinstance(hotel.adapter, DefaultPMSAdapter)

    def test_validation(self, mocker, hotel_factory):
        hotel = hotel_factory()
        hotel.inventory_days = 99
        with pytest.raises(ValidationError):
            hotel.save()

        hotel = hotel_factory()
        hotel.pms = Hotel.PMSChoices.CHANNEX
        with pytest.raises(ValidationError):
            hotel.save()

        mocker.patch(
            "backend.utils.channex_client.ChannexClient.get_properties",
            return_value=mocker.Mock(status_code=404),
        )
        hotel.pms_api_key = "test"
        hotel.pms_id = "test"
        with pytest.raises(ValidationError):
            hotel.save()

        mocker.patch(
            "backend.utils.channex_client.ChannexClient.get_properties",
            return_value=mocker.Mock(status_code=200),
        )
        mocker.patch(
            "backend.utils.channex_client.ChannexClient.get_property",
            return_value=mocker.Mock(status_code=404),
        )
        with pytest.raises(ValidationError):
            hotel.save()

    def test_invalid_pms(self, hotel_factory):
        hotel = hotel_factory()
        hotel.pms = "invalid"
        with pytest.raises(ValidationError):
            hotel.adapter

    def test_channex(self, mocked_channex_validation, hotel_factory):
        hotel = hotel_factory(channex=True)
        assert isinstance(hotel.adapter, ChannexPMSAdapter)


def test_hotel_employee_model(db):
    user = User.objects.create(
        username="test",
        email="test",
        name="test",
        role=User.UserRoleChoices.ADMIN,
    )
    with pytest.raises(ValidationError):
        HotelEmployee.objects.create(
            user=user,
            hotel=None,
        )
