from zoneinfo import ZoneInfo

from django.utils import timezone

from backend.pms.adapter import ChannexCMAdapter
from config.celery_app import app


@app.task
def handle_time_based_trigger_rule(hotel_id: int, day_ahead: int, zone_info: str):
    zone_info = ZoneInfo(zone_info)
    date = (
        timezone.now().astimezone(zone_info) + timezone.timedelta(days=day_ahead)
    ).date()
    adapter = ChannexCMAdapter(hotel_id)
    adapter.handle_time_based_trigger(date)
