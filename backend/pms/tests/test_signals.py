import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from ..models import Hotel, RatePlanRestrictions, Room
from .factories import RoomTypeFactory

User = get_user_model()

"""
We are testing the signals here, should not use the factories.
"""


def test_post_save_user(db):
    user = User.objects.create(
        username="test",
        email="test",
        name="test",
        role=User.UserRoleChoices.MANAGER,
    )
    assert user.hotel_employee is not None
    assert user.is_active is False


def test_post_save_hotel_employee(db):
    user = User.objects.create(
        username="test",
        email="test",
        name="test",
        role=User.UserRoleChoices.MANAGER,
    )
    assert user.hotel_employee is not None
    hotel = Hotel.objects.create(name="test")
    user.hotel_employee.hotel = hotel
    user.hotel_employee.save()
    assert user.is_active is True


def test_post_save_rate_plan(db, rate_plan_factory):
    rate_plan = rate_plan_factory()
    inventory_days = rate_plan.room_type.hotel.inventory_days
    assert (
        RatePlanRestrictions.objects.filter(rate_plan=rate_plan).count()
        == inventory_days + 1
    )


def test_pre_save_room(db):
    room_type = RoomTypeFactory()

    with pytest.raises(ValidationError):
        Room.objects.create(
            room_type=room_type,
            number=-1,
        )

    with pytest.raises(ValidationError):
        Room.objects.create(room_type=room_type, number=1)
        Room.objects.create(room_type=room_type, number=1)
