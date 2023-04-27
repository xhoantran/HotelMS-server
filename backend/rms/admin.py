from django.contrib import admin

from .adapter import DynamicPricingAdapter
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


admin.site.register(OccupancyBasedTriggerRule)
admin.site.register(TimeBasedTriggerRule)
