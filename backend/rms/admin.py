from typing import Any, List, Tuple

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


class DynamicPricingSettingAdmin(admin.ModelAdmin):
    list_display = [hotel_name, "is_enabled"]


admin.site.register(DynamicPricingSetting, DynamicPricingSettingAdmin)


@admin.display(description="Hotel")
def rule_hotel_name(obj):
    return obj.setting.hotel


class OccupancyBasedTriggerRuleAdmin(admin.ModelAdmin):
    list_display = [
        rule_hotel_name,
        "min_occupancy",
        "increment_factor",
        "percentage_factor",
    ]

    def get_ordering(self, request: HttpRequest) -> List[str] | Tuple[Any, ...]:
        return ["setting__hotel__name", "min_occupancy"]


admin.site.register(OccupancyBasedTriggerRule, OccupancyBasedTriggerRuleAdmin)


class TimeBasedTriggerRuleAdmin(admin.ModelAdmin):
    list_display = [
        rule_hotel_name,
        "day_ahead",
        "trigger_time",
        "min_occupancy",
        "max_occupancy",
        "increment_factor",
        "percentage_factor",
    ]

    def get_ordering(self, request: HttpRequest) -> List[str] | Tuple[Any, ...]:
        return ["setting__hotel__name", "day_ahead", "trigger_time", "min_occupancy"]


admin.site.register(TimeBasedTriggerRule, TimeBasedTriggerRuleAdmin)
