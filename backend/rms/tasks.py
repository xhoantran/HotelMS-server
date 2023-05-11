from zoneinfo import ZoneInfo

from django.utils import timezone

from backend.pms.models import RoomType
from config.celery_app import app

from .adapter import DynamicPricingAdapter


@app.task
def handle_time_based_trigger_rule(hotel_id: int, day_ahead: int, zone_info: str):
    date = (
        timezone.now().astimezone(ZoneInfo(zone_info))
        + timezone.timedelta(days=day_ahead)
    ).date()
    adapter = DynamicPricingAdapter(hotel=hotel_id)
    room_types = RoomType.objects.filter(hotel_id=hotel_id)
    updated = adapter.calculate_and_update_rates(
        room_types=room_types, dates=[date, date]
    )
    if updated:
        pass
