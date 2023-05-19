import pytest
from django.core.exceptions import ValidationError

from ..models import CMHotelConnector


def test_cm_hotel_connector_adapter(
    mocked_channex_validation, cm_hotel_connector_factory
):
    cm_hotel_connector = cm_hotel_connector_factory(channex=True)
    with pytest.raises(NotImplementedError):
        cm_hotel_connector.channel_manager = "invalid"
        cm_hotel_connector.adapter


def test_cm_hotel_connector_save(cm_hotel_connector_factory, mocker):
    with pytest.raises(ValidationError):
        cm_hotel_connector_factory(channel_manager="fake")
    mocker.patch(
        "backend.cm.adapter.ChannexAdapter.validate_api_key", return_value=False
    )

    with pytest.raises(ValidationError):
        cm_hotel_connector_factory(
            channel_manager=CMHotelConnector.ChannelManagerChoices.CHANNEX,
            cm_id="123",
            cm_api_key="123",
        )

    mocker.patch(
        "backend.cm.adapter.ChannexAdapter.validate_api_key", return_value=True
    )
    mocker.patch(
        "backend.cm.adapter.ChannexAdapter.validate_property_id",
        return_value=False,
    )
    with pytest.raises(ValidationError):
        cm_hotel_connector_factory(
            channel_manager=CMHotelConnector.ChannelManagerChoices.CHANNEX,
            cm_id="123",
            cm_api_key="123",
        )
