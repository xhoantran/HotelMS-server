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


@admin.action(description="Activate rules")
def activate_rules(modeladmin, request, queryset):
    for obj in queryset:
        DynamicPricingAdapter(setting=obj).activate_rules()


class DynamicPricingSettingAdmin(admin.ModelAdmin):
    list_display = [hotel_name, "is_enabled"]
    actions = [activate_rules]


admin.site.register(DynamicPricingSetting, DynamicPricingSettingAdmin)


admin.site.register(OccupancyBasedTriggerRule)
admin.site.register(TimeBasedTriggerRule)
