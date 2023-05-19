from django.utils import timezone

from ..models import Booking, BookingRoom, RatePlan


def test_get_room_type_inventory_map(rate_plan_factory):
    rate_plan: RatePlan = rate_plan_factory()
    hotel = rate_plan.room_type.hotel
    setting = hotel.dynamic_pricing_setting
    setting.default_base_rate = 120
    setting.is_occupancy_based = True
    setting.save()
    today = timezone.now().date()

    assert hotel.adapter.get_room_type_inventory_map(
        room_types=[rate_plan.room_type.id],
        dates=[today, today],
    ) == {
        rate_plan.room_type.id: {
            timezone.now().date(): 0,
        }
    }

    # Create booking and booking rooms
    booking = Booking.objects.create(
        hotel=hotel,
        dates=[today, today + timezone.timedelta(days=1)],
        raw_data={},
    )
    BookingRoom.objects.create(
        booking=booking,
        room_type=rate_plan.room_type,
        dates=[today, today + timezone.timedelta(days=1)],
        raw_data={},
    )
    assert hotel.adapter.get_room_type_inventory_map(
        room_types=[rate_plan.room_type.id],
        dates=[today, today + timezone.timedelta(days=1)],
    ) == {rate_plan.room_type.id: {today: 1, today + timezone.timedelta(days=1): 0}}
