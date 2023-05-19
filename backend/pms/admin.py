from typing import Any

from django.contrib import admin
from django.http.request import HttpRequest

from .models import Hotel, RatePlan, RoomType


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ("name",)
    readonly_fields = ("timezone", "currency")


@admin.display(description="Hotel")
def room_type_hotel_name(obj):
    return obj.hotel.name


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ("name", room_type_hotel_name)

    def get_ordering(self, request: HttpRequest) -> list[str] | tuple[Any, ...]:
        return ["hotel__name", "name"]


@admin.display(description="Hotel")
def rate_plan_hotel_name(obj):
    return obj.room_type.hotel.name


@admin.display(description="Room Type")
def rate_plan_room_type_name(obj):
    return obj.room_type.name


@admin.register(RatePlan)
class RatePlanAdmin(admin.ModelAdmin):
    list_display = (rate_plan_hotel_name, rate_plan_room_type_name, "name")

    def get_ordering(self, request: HttpRequest) -> list[str] | tuple[Any, ...]:
        return ["room_type__hotel__name", "room_type__name", "name"]
