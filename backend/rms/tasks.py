from django.utils import timezone

from backend.pms.adapter import ChannexPMSAdapter
from config.celery_app import app


@app.task
def handle_time_based_trigger_rule(hotel_id: int, day_ahead: int):
    date = (timezone.now() + timezone.timedelta(days=day_ahead)).date()
    adapter = ChannexPMSAdapter(hotel_id)
    adapter.handle_time_based_trigger(date)
