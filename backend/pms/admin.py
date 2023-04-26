from django.apps import apps
from django.contrib import admin

from .models import Hotel, RatePlan, RoomType

for model in apps.get_models():
    if model.__name__ and admin.site.is_registered(model):
        admin.site.unregister(model)


# PMS
admin.site.register(Hotel)
admin.site.register(RoomType)
admin.site.register(RatePlan)
