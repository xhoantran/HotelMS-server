"""
Dynamic settings will go to each hotel in hotel group.
many trigger time rule ---> Dynamic settings <---> Group -one-2-many-> RoomType

Each time rule is a periodic task.
many trigger time rule <----> periodic task -> Find group -> Find property -> Find room type -> Call handle trigger
is_active                     is_active (rule) and is_enable (rms)
"""

from config.celery_app import app


@app.task
def handle_time_rule_trigger(hotel_group_id):
    pass
