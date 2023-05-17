from django.core.mail import mail_admins
from django.db import transaction

from backend.cm.models import CMHotelConnector
from config.celery_app import app


@app.task
def setup_hotel_from_cm(channel_manager, cm_id, cm_api_key):
    with transaction.atomic():
        # Save CMHotelConnector and setup hotel
        serializer = CMHotelConnector(
            channel_manager=channel_manager,
            cm_id=cm_id,
            cm_api_key=cm_api_key,
        ).adapter.serialize_property_structure()
        cm_hotel_connector = (
            CMHotelConnector().adapter.save_serialize_property_structure(
                serializer=serializer,
                cm_api_key=cm_api_key,
            )
        )

        # Save all upcoming bookings
        cm_hotel_connector.adapter.save_all_upcoming_bookings()

        # Setup booking webhook
        cm_hotel_connector.adapter.save_booking_webhook()

        # Send email confirmation
        mail_admins(
            subject="Hotel migrated from CM successfully",
            message=f"Hotel {cm_hotel_connector.pms.name} has been migrated from CM successfully",
        )
