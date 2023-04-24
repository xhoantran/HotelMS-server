from django.apps import apps
from django.contrib import admin

from backend.rms.models import DynamicPricingSetting, OccupancyBasedTriggerRule

from .models import Hotel, HotelGroup, RatePlan, RoomType

for model in apps.get_models():
    if model.__name__ and admin.site.is_registered(model):
        admin.site.unregister(model)


# PMS
admin.site.register(HotelGroup)
admin.site.register(Hotel)
admin.site.register(RoomType)
admin.site.register(RatePlan)

# RMS
admin.site.register(DynamicPricingSetting)
admin.site.register(OccupancyBasedTriggerRule)


# admin.site.register(PeriodicTask)
# admin.site.register(PeriodicTasks)
# admin.site.register(IntervalSchedule)
# admin.site.register(CrontabSchedule)
