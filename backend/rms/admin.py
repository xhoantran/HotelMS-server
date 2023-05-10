from typing import Any

from django.contrib import admin
from django.http.request import HttpRequest

from .models import (
    DynamicPricingSetting,
    OccupancyBasedTriggerRule,
    TimeBasedTriggerRule,
)


@admin.display(description="Hotel")
def hotel_name(obj):
    return obj.hotel


@admin.register(DynamicPricingSetting)
class DynamicPricingSettingAdmin(admin.ModelAdmin):
    list_display = [hotel_name, "is_enabled"]


@admin.display(description="Hotel")
def rule_hotel_name(obj):
    return obj.setting.hotel


@admin.register(OccupancyBasedTriggerRule)
class OccupancyBasedTriggerRuleAdmin(admin.ModelAdmin):
    list_display = [
        rule_hotel_name,
        "min_occupancy",
        "increment_factor",
        "percentage_factor",
    ]

    def get_ordering(self, request: HttpRequest) -> list[str] | tuple[Any, ...]:
        return ["setting__hotel__name", "min_occupancy"]


@admin.register(TimeBasedTriggerRule)
class TimeBasedTriggerRuleAdmin(admin.ModelAdmin):
    list_display = [
        rule_hotel_name,
        "day_ahead",
        "hour",
        "min_occupancy",
        "increment_factor",
        "percentage_factor",
    ]

    def get_ordering(self, request: HttpRequest) -> list[str] | tuple[Any, ...]:
        return ["setting__hotel__name", "day_ahead", "hour", "minute", "min_occupancy"]
