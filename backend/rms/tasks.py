from zoneinfo import ZoneInfo

from django.db import transaction
from django.utils import timezone

from backend.cm.models import CMHotelConnector
from backend.pms.models import RoomType
from backend.rms.models import DynamicPricingSetting
from config.celery_app import app

from .adapter import DynamicPricingAdapter


@app.task
def recalculate_all_rate(dynamic_pricing_setting_id: int):
    with transaction.atomic():
        dynamic_pricing_setting = DynamicPricingSetting.objects.get(
            id=dynamic_pricing_setting_id
        )
        hotel = dynamic_pricing_setting.hotel
        adapter = DynamicPricingAdapter(hotel=hotel)
        room_types = RoomType.objects.filter(hotel=hotel).values_list("id", flat=True)
        today = timezone.now().astimezone(hotel.timezone).date()
        new_restrictions = adapter.calculate_and_update_rates(
            room_types=room_types,
            dates=[
                today,
                today + timezone.timedelta(days=hotel.inventory_days),
            ],
        )
        if new_restrictions:
            cm_hotel_connector = CMHotelConnector.objects.get(pms=hotel)
            cm_hotel_connector.adapter.save_rate_plan_restrictions(
                new_rate_plan_restrictions=new_restrictions
            )


@app.task
def handle_occupancy_based_trigger(
    hotel_id: int, room_types: list[int], dates: tuple[str, str]
):
    with transaction.atomic():
        adapter = DynamicPricingAdapter(hotel=hotel_id)
        new_restrictions = adapter.calculate_and_update_rates(
            room_types=room_types,
            dates=(
                timezone.datetime.strptime(dates[0], "%Y-%m-%d").date(),
                timezone.datetime.strptime(dates[1], "%Y-%m-%d").date(),
            ),
        )
        if new_restrictions:
            cm_hotel_connector = CMHotelConnector.objects.get(hotel_id=hotel_id)
            cm_hotel_connector.adapter.save_rate_plan_restrictions(
                new_rate_plan_restrictions=new_restrictions
            )


@app.task
def handle_time_based_trigger(hotel_id: int, day_ahead: int, zone_info: str):
    with transaction.atomic():
        date = (
            timezone.now().astimezone(ZoneInfo(zone_info))
            + timezone.timedelta(days=day_ahead)
        ).date()
        adapter = DynamicPricingAdapter(hotel=hotel_id)
        room_types = RoomType.objects.filter(hotel_id=hotel_id).values_list(
            "id", flat=True
        )
        new_restrictions = adapter.calculate_and_update_rates(
            room_types=room_types, dates=[date, date]
        )
        if new_restrictions:
            cm_hotel_connector = CMHotelConnector.objects.get(hotel_id=hotel_id)
            cm_hotel_connector.adapter.save_rate_plan_restrictions(
                new_rate_plan_restrictions=new_restrictions
            )
