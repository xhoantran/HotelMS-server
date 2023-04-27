from django.apps import apps
from django.contrib import admin

from .models import Hotel, HotelAPIKey, RatePlan, RoomType

for model in apps.get_models():
    if model.__name__ and admin.site.is_registered(model):
        admin.site.unregister(model)


@admin.action(description="Sync with Channex")
def sync_with_channex(modeladmin, request, queryset):
    for hotel in queryset:
        if hotel.pms == Hotel.PMSChoices.CHANNEX:
            HotelAPIKey.objects.get(hotel=hotel).delete()
            _, api_key = HotelAPIKey.objects.create_key(hotel=hotel, name="API Key")
            hotel.adapter.sync_up(api_key=api_key)


class HotelAdmin(admin.ModelAdmin):
    actions = [sync_with_channex]


admin.site.register(Hotel, HotelAdmin)
admin.site.register(RoomType)
admin.site.register(RatePlan)
