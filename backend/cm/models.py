from django.core.exceptions import ValidationError
from django.db import models
from rest_framework_api_key.models import AbstractAPIKey

from backend.pms.models import Booking, Hotel, RatePlan, RoomType


class CMHotelConnector(models.Model):
    pms = models.OneToOneField(
        Hotel,
        on_delete=models.CASCADE,
        related_name="channel_manager_connector",
    )

    class ChannelManagerChoices(models.TextChoices):
        CHANNEX = "Channex", "Channex"

    channel_manager = models.CharField(
        max_length=16,
        choices=ChannelManagerChoices.choices,
        default=ChannelManagerChoices.CHANNEX,
    )
    cm_name = models.CharField(max_length=255, null=True, blank=True)
    cm_id = models.UUIDField()
    cm_api_key = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["channel_manager", "cm_id"],
                name="unique_cm_id_per_channel_manager",
                violation_error_message="Property with this external ID already exists",
            )
        ]

    @property
    def adapter(self):
        if self.channel_manager == self.ChannelManagerChoices.CHANNEX:
            from .adapter import ChannexAdapter

            return ChannexAdapter(self)
        else:
            raise NotImplementedError

    def validate_cm(self, *args, **kwargs):
        if self.channel_manager not in self.ChannelManagerChoices.values:
            raise ValidationError("Invalid channel manager")
        if not self.adapter.validate_api_key(self.cm_api_key):
            raise ValidationError("Invalid channel manager API key")
        if not self.adapter.validate_property_id(
            api_key=self.cm_api_key,
            property_id=self.cm_id,
        ):
            raise ValidationError("Invalid channel manager ID")

    def save(self, *args, **kwargs):
        self.validate_cm()
        super().save(*args, **kwargs)


class CMHotelConnectorAPIKey(AbstractAPIKey):
    cm_hotel_connector = models.OneToOneField(
        CMHotelConnector,
        on_delete=models.CASCADE,
        related_name="api_key",
    )


class CMRoomTypeConnector(models.Model):
    cm_hotel_connector = models.ForeignKey(
        CMHotelConnector,
        on_delete=models.CASCADE,
        related_name="room_type_connectors",
    )
    pms = models.OneToOneField(
        RoomType,
        on_delete=models.CASCADE,
        related_name="channel_manager_connector",
        blank=True,
        null=True,
    )
    cm_name = models.CharField(max_length=255)
    cm_id = models.UUIDField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cm_hotel_connector", "cm_id"],
                name="unique_room_type_cm_id_per_hotel_connector",
                violation_error_message="Room type with this external ID already associated with this property",
            )
        ]


class CMRatePlanConnector(models.Model):
    cm_room_type_connector = models.ForeignKey(
        CMRoomTypeConnector,
        on_delete=models.CASCADE,
        related_name="rate_plan_connectors",
    )
    pms = models.OneToOneField(
        RatePlan,
        on_delete=models.CASCADE,
        related_name="channel_manager_connector",
        blank=True,
        null=True,
    )
    cm_name = models.CharField(max_length=255)
    cm_id = models.UUIDField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cm_room_type_connector", "cm_id"],
                name="unique_rate_plan_cm_id_per_room_type_connector",
                violation_error_message="Rate plan with this external ID already associated with this room type",
            )
        ]


class CMBookingConnector(models.Model):
    cm_hotel_connector = models.ForeignKey(
        CMHotelConnector,
        on_delete=models.CASCADE,
        related_name="booking_connectors",
    )
    pms = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name="channel_manager_connector",
        blank=True,
        null=True,
    )
    cm_id = models.UUIDField(null=True, blank=True)
    inserted_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cm_hotel_connector", "cm_id"],
                name="unique_booking_cm_id_per_hotel_connector",
                violation_error_message="Booking with this external ID already associated with this property",
            )
        ]
