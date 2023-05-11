from django.core.exceptions import ValidationError
from django.db import models
from rest_framework_api_key.models import AbstractAPIKey


class CMHotel(models.Model):
    hotel = models.OneToOneField(
        "pms.Hotel",
        on_delete=models.CASCADE,
        related_name="channel_management",
    )

    class CMChoices(models.TextChoices):
        CHANNEX = "CHANNEX", "Channex"
        __empty__ = "default"

    cm = models.CharField(
        max_length=16,
        choices=CMChoices.choices,
        blank=True,
    )
    cm_id = models.UUIDField(null=True, blank=True)
    cm_api_key = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cm", "cm_id"],
                name="unique_cm_id_per_cm",
                violation_error_message="Property with this external ID already exists",
            )
        ]

    @property
    def adapter(self):
        if self.cm == self.CMChoices.CHANNEX:
            from .adapter import ChannexCMAdapter

            return ChannexCMAdapter(self)
        else:
            raise NotImplementedError(f"CM {self.cm} is not implemented")

    def validate_cm(self):
        if not self.cm:
            return
        if not self.cm_id or not self.cm_api_key:
            raise ValidationError(
                "External ID and API Key are required for external CM"
            )
        if not self.adapter.validate_api_key(self.cm_api_key):
            raise ValidationError("Invalid API Key")
        if not self.adapter.validate_cm_id(self.cm_api_key, self.cm_id):
            raise ValidationError("Invalid external ID")

    def save(self, *args, **kwargs):
        self.validate_cm()
        super().save(*args, **kwargs)


class HotelAPIKey(AbstractAPIKey):
    hotel = models.OneToOneField(
        CMHotel,
        on_delete=models.CASCADE,
        related_name="api_key",
    )


class CMRoomType(models.Model):
    room_type = models.OneToOneField(
        "pms.RoomType",
        on_delete=models.CASCADE,
        related_name="channel_management",
    )
    cm_id = models.UUIDField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["room_type", "cm_id"],
                name="unique_cm_id_per_room_type",
                violation_error_message="Room type with this external ID already exists",
            )
        ]


class CMRatePlan(models.Model):
    rate_plan = models.OneToOneField(
        "pms.RatePlan",
        on_delete=models.CASCADE,
        related_name="channel_management",
    )
    cm_id = models.UUIDField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["rate_plan", "cm_id"],
                name="unique_cm_id_per_rate_plan",
                violation_error_message="Rate plan with this external ID already exists",
            )
        ]
