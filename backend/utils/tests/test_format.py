import pytest

from backend.pms.models import Hotel

from ..format import convert_to_id, convert_to_obj


def test_convert_to_id(hotel_factory):
    hotel = hotel_factory()

    assert convert_to_id(hotel, Hotel) == hotel.id
    assert convert_to_id(hotel.id, Hotel) == hotel.id

    with pytest.raises(TypeError):
        convert_to_id(object, Hotel)


def test_convert_to_obj(hotel_factory):
    hotel = hotel_factory()

    assert convert_to_obj(hotel, Hotel) == hotel
    assert convert_to_obj(hotel.id, Hotel) == hotel

    with pytest.raises(TypeError):
        convert_to_obj(object, Hotel)
