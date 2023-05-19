from typing import Any

from rest_framework import serializers

from backend.pms.serializers import HotelSerializer

from .models import CMHotelConnector, CMRatePlanConnector, CMRoomTypeConnector


class CMRatePlanConnectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = CMRatePlanConnector
        fields = ("cm_name", "cm_id")


class CMRoomTypeConnectorSerializer(serializers.ModelSerializer):
    cm_rate_plan_connectors = CMRatePlanConnectorSerializer(many=True)

    class Meta:
        model = CMRoomTypeConnector
        fields = ("cm_name", "cm_id", "cm_rate_plan_connectors")


class CMHotelConnectorSerializer(serializers.ModelSerializer):
    cm_room_type_connectors = CMRoomTypeConnectorSerializer(many=True, read_only=True)
    pms = HotelSerializer(read_only=True)

    class Meta:
        model = CMHotelConnector
        fields = (
            "channel_manager",
            "cm_name",
            "cm_id",
            "cm_api_key",
            "cm_room_type_connectors",
            "pms",
        )
        extra_kwargs = {
            "cm_api_key": {"write_only": True},
            "cm_name": {"read_only": True},
        }


class PreviewHotelSerializer(serializers.Serializer):
    channel_manager = serializers.CharField()
    cm_id = serializers.CharField()
    cm_api_key = serializers.CharField()


class SetupHotelSerializer(PreviewHotelSerializer):
    def validate(self, attrs: Any) -> Any:
        attrs = super().validate(attrs)

        # Validate channel manager
        CMHotelConnector(
            channel_manager=attrs["channel_manager"],
            cm_id=attrs["cm_id"],
            cm_api_key=attrs["cm_api_key"],
        ).validate_cm()

        # Validate existing CMHotelConnector
        if CMHotelConnector.objects.filter(
            channel_manager=attrs["channel_manager"], cm_id=attrs["cm_id"]
        ).exists():
            raise serializers.ValidationError(
                "This property already exists.", code="unique"
            )

        return attrs
