from django.contrib import admin

from backend.rms.models import (
    DynamicPricingSetting,
    OccupancyBasedTriggerRule,
    TimeBasedTriggerRule,
)

# RMS
admin.site.register(DynamicPricingSetting)
admin.site.register(OccupancyBasedTriggerRule)
admin.site.register(TimeBasedTriggerRule)
