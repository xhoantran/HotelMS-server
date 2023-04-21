from django.apps import apps
from django.contrib import admin

from backend.rms.models import AvailabilityBasedTriggerRule, DynamicPricingSetting

from .models import Hotel, HotelGroup, RatePlan, RoomType

for model in apps.get_models():
    if model.__name__ and admin.site.is_registered(model):
        admin.site.unregister(model)

admin.site.register(HotelGroup)
admin.site.register(Hotel)
admin.site.register(RoomType)
admin.site.register(RatePlan)
admin.site.register(DynamicPricingSetting)
admin.site.register(AvailabilityBasedTriggerRule)
