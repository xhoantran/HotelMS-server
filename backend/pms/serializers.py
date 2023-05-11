from django.contrib.auth import get_user_model
from rest_framework import serializers
from timezone_field.rest_framework import TimeZoneSerializerField

from backend.rms.serializers import DynamicPricingSettingReadOnlySerializer

from .models import Hotel, HotelEmployee, RatePlan, RatePlanRestrictions, Room, RoomType

User = get_user_model()


class HotelSerializer(serializers.ModelSerializer):
    timezone = TimeZoneSerializerField(use_pytz=False, read_only=True)
    dynamic_pricing_setting = DynamicPricingSettingReadOnlySerializer(
        read_only=True, required=False
    )

    class Meta:
        model = Hotel
        exclude = ("id",)


class HotelEmployeeSerializer(serializers.ModelSerializer):
    hotel = serializers.SlugRelatedField(
        slug_field="uuid", queryset=Hotel.objects.all()
    )

    class Meta:
        model = HotelEmployee
        exclude = ("id",)


class RatePlanSerializer(serializers.ModelSerializer):
    room_type = serializers.SlugRelatedField(
        slug_field="uuid", queryset=RoomType.objects.all()
    )

    class Meta:
        model = RatePlan
        exclude = ("id",)

    # TODO: validate room_type belongs to hotel


class RoomTypeSerializer(serializers.ModelSerializer):
    hotel = serializers.SlugRelatedField(
        slug_field="uuid", queryset=Hotel.objects.all()
    )
    rate_plans = RatePlanSerializer(many=True, read_only=True)

    class Meta:
        model = RoomType
        exclude = ("id",)

    def validate_hotel(self, value):
        if (
            self.context["request"].user.role != User.UserRoleChoices.ADMIN
            and value != self.context["request"].user.hotel_employee.hotel
        ):
            raise serializers.ValidationError(
                "You can only create room types for your hotel"
            )
        return value


class RatePlanRestrictionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RatePlanRestrictions
        exclude = ("id", "rate_plan")


class RoomSerializer(serializers.ModelSerializer):
    room_type = serializers.SlugRelatedField(
        slug_field="uuid", queryset=RoomType.objects.all()
    )

    class Meta:
        model = Room
        exclude = ("id",)

    def validate_room_type(self, value):
        if (
            self.context["request"].user.role != User.UserRoleChoices.ADMIN
            and value.hotel != self.context["request"].user.hotel_employee.hotel
        ):
            raise serializers.ValidationError(
                "You can only create rooms for your hotel"
            )
        return value
