import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from ..models import HotelEmployee

User = get_user_model()


def test_hotel_validation(hotel_factory):
    hotel = hotel_factory()
    hotel.inventory_days = 99
    with pytest.raises(ValidationError):
        hotel.save()


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
