from datetime import date as date_class
from datetime import timedelta

from django.db.models import Q


class HotelAdapter:
    def __init__(self, hotel):
        self.hotel = hotel

    @staticmethod
    def daterange(start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + timedelta(days=n)

    def get_room_type_inventory_map(
        self, room_types: list[int], dates: tuple[date_class, date_class]
    ):
        from .models import Booking, BookingRoom

        booked_room_type = BookingRoom.objects.filter(
            ~Q(booking__status=Booking.StatusChoices.CANCELLED),
            dates__overlap=dates,
            room_type__in=room_types,
        ).values("room_type", "dates")

        # Initialize room type inventory map
        room_type_inventory_map = {}
        for room_type in room_types:
            room_type_inventory_map[room_type] = {}
            for date in self.daterange(dates[0], dates[1] + timedelta(days=1)):
                room_type_inventory_map[room_type][date] = 0

        # Update room type inventory map
        for booking_room in booked_room_type:
            lower = booking_room["dates"].lower
            upper = booking_room["dates"].upper
            for date in self.daterange(lower, upper):
                room_type_inventory_map[booking_room["room_type"]][date] += 1

        return room_type_inventory_map
