import uuid

from django.contrib.auth import get_user_model
from django.db import models
from rest_framework_api_key.models import AbstractAPIKey

User = get_user_model()


class HotelGroup(models.Model):
    name = models.CharField(max_length=255)


class Hotel(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=255)
    inventory_days = models.SmallIntegerField(default=100)
    group = models.ForeignKey(
        HotelGroup,
        on_delete=models.PROTECT,
        related_name="hotels",
        null=True,
        blank=True,
    )

    class PMSChoices(models.TextChoices):
        CHANNEX = "CHANNEX", "Channex"
        __empty__ = "default"

    pms = models.CharField(
        max_length=16,
        choices=PMSChoices.choices,
        default=PMSChoices.__empty__,
    )
    pms_id = models.UUIDField(null=True, blank=True)
    # TODO: This should be encrypted in production
    pms_api_key = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        unique_together = ("pms", "pms_id")

    @property
    def adapter(self):
        if self.pms == self.PMSChoices.CHANNEX:
            from .adapter import ChannexPMSAdapter

            return ChannexPMSAdapter(self)
        elif self.pms == self.PMSChoices.__empty__:
            from .adapter import DefaultPMSAdapter

            return DefaultPMSAdapter(self)
        else:
            raise ValueError("Invalid PMS")

    def validate_pms(self):
        if self.pms != self.PMSChoices.__empty__:
            if not self.pms_id or not self.pms_api_key:
                raise ValueError(
                    "External ID and API Key are required for external PMS"
                )
            if not self.adapter.validate_api_key(self.pms_api_key):
                raise ValueError("Invalid API Key")
            if not self.adapter.validate_pms_id(self.pms_api_key, self.pms_id):
                raise ValueError("Invalid external ID")

    def save(self, *args, **kwargs):
        if self.inventory_days < 100 or self.inventory_days > 700:
            raise ValueError("Inventory days must be between 100 and 700")
        self.validate_pms()
        super().save(*args, **kwargs)


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
            raise ValueError("Hotel employee must be a manager, receptionist or staff")
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

    class Meta:
        unique_together = ("hotel", "pms_id")


class RoomTypeAvailability(models.Model):
    room_type = models.ForeignKey(
        RoomType,
        on_delete=models.CASCADE,
        related_name="availability",
    )
    date = models.DateField()
    availability = models.SmallIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("room_type", "date")


class RatePlan(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=64)
    room_type = models.ForeignKey(
        RoomType,
        on_delete=models.CASCADE,
        related_name="rate_plans",
    )
    pms_id = models.UUIDField(null=True, blank=True)

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
