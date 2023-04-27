from typing import Any

from django.apps import apps
from django.contrib import admin
from django.db.models.query import QuerySet
from django.http.request import HttpRequest

from .models import Hotel, HotelAPIKey, RatePlan, RoomType

for model in apps.get_models():
    if model.__name__ and admin.site.is_registered(model):
        admin.site.unregister(model)


@admin.action(description="Sync with Channex")
def sync_with_channex(modeladmin, request, queryset: QuerySet[Hotel]):
    for hotel in queryset:
        if hotel.pms == Hotel.PMSChoices.CHANNEX:
            HotelAPIKey.objects.get(hotel=hotel).delete()
            _, api_key = HotelAPIKey.objects.create_key(hotel=hotel, name="API Key")
            hotel.adapter.sync_up(api_key=api_key)


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ("name", "pms", "pms_id")
    actions = [sync_with_channex]


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "hotel", "pms_id")

    def get_ordering(self, request: HttpRequest) -> list[str] | tuple[Any, ...]:
        return ["hotel__name", "name"]


@admin.display(description="Hotel")
def rate_plan_hotel_name(obj):
    return obj.room_type.hotel


@admin.register(RatePlan)
class RatePlanAdmin(admin.ModelAdmin):
    list_display = (rate_plan_hotel_name, "room_type", "name", "pms_id")

    def get_ordering(self, request: HttpRequest) -> list[str] | tuple[Any, ...]:
        return ["room_type__hotel__name", "room_type__name", "name"]
