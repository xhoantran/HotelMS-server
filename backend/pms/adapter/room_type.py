from datetime import datetime

from django.core.exceptions import ValidationError
from django.db.models import Count, Q

from ..models import RoomType


class RoomTypeAdapter:
    def __init__(self, room_type: RoomType):
        self.room_type = room_type

    @staticmethod
    def _clean_date_range(start_date, end_date) -> None:
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date is None:
            return start_date
        if end_date < start_date:
            raise ValidationError("End date must be greater or equal to start date")
        return start_date

    def _get_booked_rooms(self, start_date, end_date=None):
        end_date = self._clean_date_range(start_date, end_date)
        return (
            self.room_type.rooms.filter(
                bookings__start_date__lte=end_date,
                bookings__end_date__gte=start_date,
                bookings__is_cancelled=False,
            )
            .annotate(num_bookings=Count("bookings"))
            .filter(num_bookings__gt=0)
        )

    def count_booked_rooms(self, start_date, end_date=None) -> int:
        return self._get_booked_rooms(start_date, end_date).count()

    def _get_available_rooms(self, start_date, end_date=None):
        end_date = self._clean_date_range(start_date, end_date)
        return self.room_type.rooms.annotate(
            num_bookings=Count(
                "bookings",
                filter=Q(
                    bookings__start_date__lte=end_date,
                    bookings__end_date__gte=start_date,
                    bookings__is_cancelled=False,
                ),
            )
        ).filter(num_bookings=0)

    def get_available_room(self, start_date, end_date=None):
        # TODO: Integrate with OptaPlanner?
        return self._get_available_rooms(start_date, end_date).first()

    def count_available_rooms(self, start_date, end_date=None) -> int:
        return self._get_available_rooms(start_date, end_date).count()

    def is_available(self, start_date, end_date=None) -> bool:
        return self._get_available_rooms(
            start_date=start_date,
            end_date=end_date,
        ).exists()
