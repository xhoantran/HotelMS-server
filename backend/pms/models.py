import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from rest_framework_api_key.models import AbstractAPIKey
from timezone_field import TimeZoneField

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

    class PMSChoices(models.TextChoices):
        CHANNEX = "CHANNEX", "Channex"
        __empty__ = "default"

    pms = models.CharField(
        max_length=16,
        choices=PMSChoices.choices,
        blank=True,
    )
    pms_id = models.UUIDField(null=True, blank=True)
    # TODO: This should be encrypted in production
    pms_api_key = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["pms", "pms_id"],
                name="unique_pms_id_per_pms",
                violation_error_message="Property with this external ID already exists",
            )
        ]

    @property
    def adapter(self):
        if self.pms == self.PMSChoices.CHANNEX:
            from .adapter import ChannexPMSAdapter

            return ChannexPMSAdapter(self)
        elif not self.pms:
            from .adapter import DefaultPMSAdapter

            return DefaultPMSAdapter(self)
        else:
            raise ValidationError("Invalid PMS")

    def validate_pms(self):
        if not self.pms:
            return
        if not self.pms_id or not self.pms_api_key:
            raise ValidationError(
                "External ID and API Key are required for external PMS"
            )
        if not self.adapter.validate_api_key(self.pms_api_key):
            raise ValidationError("Invalid API Key")
        if not self.adapter.validate_pms_id(self.pms_api_key, self.pms_id):
            raise ValidationError("Invalid external ID")

    def save(self, *args, **kwargs):
        if self.inventory_days < 100 or self.inventory_days > 700:
            raise ValidationError("Inventory days must be between 100 and 700")
        self.validate_pms()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class HotelAPIKey(AbstractAPIKey):
    hotel = models.OneToOneField(
        Hotel,
        on_delete=models.CASCADE,
        related_name="api_key",
    )


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
    number_of_beds = models.SmallIntegerField(default=0)
    base_rate = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    pms_id = models.UUIDField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("hotel", "pms_id")

    def __str__(self) -> str:
        return self.name


class RatePlan(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=64)
    room_type = models.ForeignKey(
        RoomType,
        on_delete=models.CASCADE,
        related_name="rate_plans",
    )
    pms_id = models.UUIDField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("room_type", "pms_id")


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

    def __str__(self) -> str:
        return f"{self.rate_plan} - {self.date}"


class Room(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    number = models.IntegerField()
    room_type = models.ForeignKey(
        RoomType,
        on_delete=models.CASCADE,
        related_name="rooms",
    )


# Deprecated
class Booking(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="bookings",
        limit_choices_to={"role": User.UserRoleChoices.GUEST},
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    rate = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    is_cancelled = models.BooleanField(default=False)

    # is_checked_in = models.BooleanField(default=False)
    # check_in = models.DateTimeField(null=True, blank=True)
    # check_out = models.DateTimeField(null=True, blank=True)

    @property
    def number_of_nights(self):
        return (self.end_date - self.start_date).days

    @property
    def total_rate(self):
        return self.rate * self.number_of_nights
