import uuid

from django.contrib.auth import get_user_model
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateRangeField, RangeOperators
from django.core.exceptions import ValidationError
from django.db import models
from timezone_field import TimeZoneField

from .adapter import HotelAdapter

User = get_user_model()


class Hotel(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=255)
    inventory_days = models.SmallIntegerField(default=100)

    address = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=128, null=True, blank=True)
    country = models.CharField(max_length=2, null=True, blank=True)
    currency = models.CharField(max_length=3, null=True, blank=True)
    # TODO: Add logic to derive this from the city and country
    timezone = TimeZoneField(use_pytz=False, default="UTC")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def adapter(self):
        return HotelAdapter(self)

    def save(self, *args, **kwargs):
        if self.inventory_days < 100 or self.inventory_days > 700:
            raise ValidationError("Inventory days must be between 100 and 700")
        super().save(*args, **kwargs)


class HotelEmployee(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="hotel_employee",
    )
    hotel = models.ForeignKey(
        Hotel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        unique_together = ("user", "hotel")

    def save(self, *args, **kwargs):
        if self.user.role not in (
            User.UserRoleChoices.MANAGER,
            User.UserRoleChoices.RECEPTIONIST,
            User.UserRoleChoices.STAFF,
        ):
            raise ValidationError(
                "Hotel employee must be a manager, receptionist or staff"
            )
        super().save(*args, **kwargs)


class RoomType(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    hotel = models.ForeignKey(
        Hotel,
        on_delete=models.CASCADE,
        related_name="room_types",
    )
    name = models.CharField(max_length=64)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class RatePlan(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    room_type = models.ForeignKey(
        RoomType,
        on_delete=models.CASCADE,
        related_name="rate_plans",
    )
    name = models.CharField(max_length=64)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class RatePlanRestrictions(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    rate_plan = models.ForeignKey(
        RatePlan,
        on_delete=models.CASCADE,
        related_name="restrictions",
    )
    date = models.DateField()
    rate = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("rate_plan", "date")


class Room(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    number = models.IntegerField()
    room_type = models.ForeignKey(
        RoomType,
        on_delete=models.CASCADE,
        related_name="rooms",
    )


class Booking(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    hotel = models.ForeignKey(
        Hotel,
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    dates = DateRangeField()

    class StatusChoices(models.TextChoices):
        NEW = "new", "New"
        CANCELLED = "cancelled", "Cancelled"
        MODIFIED = "modified", "Modified"

    status = models.CharField(
        max_length=16,
        choices=StatusChoices.choices,
        default=StatusChoices.NEW,
    )

    raw_data = models.JSONField()


class BookingRoom(models.Model):
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="booking_rooms",
    )
    room_type = models.ForeignKey(
        RoomType,
        on_delete=models.PROTECT,
        related_name="booking_rooms",
        blank=True,
        null=True,
    )
    dates = DateRangeField()
    raw_data = models.JSONField()

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name="booking_rooms",
        blank=True,
        null=True,
    )

    class Meta:
        constraints = [
            ExclusionConstraint(
                expressions=[
                    ("dates", RangeOperators.OVERLAPS),
                    ("room", RangeOperators.EQUAL),
                ],
                name="exclude_overlapping_dates_for_room",
            ),
        ]
        indexes = [
            models.Index(fields=["dates", "room_type"]),
        ]
