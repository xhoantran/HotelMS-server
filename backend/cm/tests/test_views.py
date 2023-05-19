import uuid

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from backend.pms.models import Booking

from ..models import CMBookingConnector, CMHotelConnector, CMHotelConnectorAPIKey


def test_preview_hotel_api_view(
    admin,
    get_api_client,
    mocked_channex_setup_hotel,
):
    url = reverse("cm:hotel-preview")
    admin_api_client = get_api_client(admin)

    data = mocked_channex_setup_hotel

    response = admin_api_client.post(
        url,
        data={
            "channel_manager": CMHotelConnector.ChannelManagerChoices.CHANNEX,
            "cm_id": data["hotel_id"],
            "cm_api_key": "valid_api_key",
        },
    )
    assert response.status_code == status.HTTP_200_OK


def test_setup_hotel_api_view(
    mocked_channex_validation,
    admin,
    get_api_client,
    mocked_channex_setup_hotel,
    settings,
):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    url = reverse("cm:hotel-setup")
    admin_api_client = get_api_client(admin)

    data = mocked_channex_setup_hotel

    response = admin_api_client.post(
        url,
        data={
            "channel_manager": CMHotelConnector.ChannelManagerChoices.CHANNEX,
            "cm_id": data["hotel_id"],
            "cm_api_key": "valid_api_key",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert CMHotelConnector.objects.count() == 1


def test_cm_booking_webhook_trigger_invalid_api_key(db):
    url = reverse("cm:webhook-booking")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Api-Key invalid_api_key")

    response = client.post(url, data={})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_cm_booking_webhook_trigger_integration(
    mocked_channex_validation,
    mocker,
    admin,
    get_api_client,
    mocked_channex_setup_hotel,
    settings,
):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    url = reverse("cm:hotel-setup")
    admin_api_client = get_api_client(admin)
    data = mocked_channex_setup_hotel
    admin_api_client.post(
        url,
        data={
            "channel_manager": CMHotelConnector.ChannelManagerChoices.CHANNEX,
            "cm_id": data["hotel_id"],
            "cm_api_key": "valid_api_key",
        },
    )

    assert CMHotelConnector.objects.count() == 1

    # Get the internal API Key
    cm_hotel_connector = CMHotelConnector.objects.get(
        channel_manager=CMHotelConnector.ChannelManagerChoices.CHANNEX,
        cm_id=data["hotel_id"],
    )
    CMHotelConnectorAPIKey.objects.get(cm_hotel_connector=cm_hotel_connector).delete()
    _, api_key = CMHotelConnectorAPIKey.objects.create_key(
        cm_hotel_connector=cm_hotel_connector, name="valid_api_key"
    )

    mocked_calculate_rates = mocker.patch(
        "backend.rms.adapter.DynamicPricingAdapter.calculate_and_update_rates",
        return_value=[],
    )

    # Setup the client
    url = reverse("cm:webhook-booking")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Api-Key {api_key}")

    # New booking
    booking_cm_id = "4e390174-75a9-4989-bd43-b96fac279e8e"
    revision_cm_id = str(uuid.uuid4())
    mocker.patch(
        "backend.cm.client.channex.ChannexClient.get_booking_revision",
        return_value={
            "attributes": {
                "arrival_date": "2023-05-17",
                "booking_id": booking_cm_id,
                "departure_date": "2023-05-19",
                "id": revision_cm_id,
                "property_id": data["hotel_id"],
                "rooms": [
                    {
                        "checkin_date": "2023-05-17",
                        "checkout_date": "2023-05-19",
                        "rate_plan_id": data["rate_plan_1_id"],
                        "room_type_id": data["room_type_1_id"],
                    }
                ],
                "status": "new",
            },
            "id": revision_cm_id,
            "type": "booking_revision",
        },
    )
    response = client.post(
        url,
        data={
            "event": "booking_new",
            "payload": {
                "amount": "1240000",
                "arrival_date": "2023-05-17",
                "booking_id": booking_cm_id,
                "booking_revision_id": revision_cm_id,
                "booking_unique_id": "BDC-3611227021",
                "channel_id": "4f152895-b5c3-4c27-bc02-a99dc0f01072",
                "count_of_nights": 2,
                "count_of_rooms": 1,
                "currency": "VND",
                "customer_name": "Test Test",
                "live_feed_event_id": "cbadb500-151b-45a6-a44b-9b685e8bd802",
                "ota_code": "3611227021",
                "property_id": data["hotel_id"],
            },
            "property_id": data["hotel_id"],
            "timestamp": "2023-05-15T19:42:35.858695Z",
            "user_id": None,
        },
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    cm_booking_connector = CMBookingConnector.objects.get(
        cm_id=booking_cm_id,
        cm_hotel_connector=cm_hotel_connector,
    )
    assert cm_booking_connector.pms.status == Booking.StatusChoices.NEW
    assert cm_booking_connector.pms.booking_rooms.count() == 1
    assert mocked_calculate_rates.call_count == 1

    # Update booking with new revision (status modified)
    revision_cm_id = str(uuid.uuid4())
    mocker.patch(
        "backend.cm.client.channex.ChannexClient.get_booking_revision",
        return_value={
            "attributes": {
                "arrival_date": "2023-05-18",
                "booking_id": booking_cm_id,
                "departure_date": "2023-05-20",
                "id": revision_cm_id,
                "property_id": data["hotel_id"],
                "rooms": [
                    {
                        "checkin_date": "2023-05-18",
                        "checkout_date": "2023-05-20",
                        "rate_plan_id": data["rate_plan_1_id"],
                        "room_type_id": data["room_type_1_id"],
                    }
                ],
                "status": "modified",
            },
            "id": revision_cm_id,
            "type": "booking_revision",
        },
    )
    response = client.post(
        url,
        data={
            "event": "booking_modification",
            "payload": {
                "amount": "1240000",
                "arrival_date": "2023-05-18",
                "booking_id": booking_cm_id,
                "booking_revision_id": revision_cm_id,
                "booking_unique_id": "BDC-3611227021",
                "channel_id": "4f152895-b5c3-4c27-bc02-a99dc0f01072",
                "count_of_nights": 2,
                "count_of_rooms": 1,
                "currency": "VND",
                "customer_name": "Test Test",
                "live_feed_event_id": "cbadb500-151b-45a6-a44b-9b685e8bd802",
                "ota_code": "3611227021",
                "property_id": data["hotel_id"],
            },
            "property_id": data["hotel_id"],
            "timestamp": "2023-05-15T19:42:35.858695Z",
            "user_id": None,
        },
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert mocked_calculate_rates.call_count == 2

    # Cancel booking with new revision (status cancelled)
    revision_cm_id = str(uuid.uuid4())
    mocker.patch(
        "backend.cm.client.channex.ChannexClient.get_booking_revision",
        return_value={
            "attributes": {
                "arrival_date": "2023-05-18",
                "booking_id": booking_cm_id,
                "departure_date": "2023-05-20",
                "id": revision_cm_id,
                "property_id": data["hotel_id"],
                "rooms": [
                    {
                        "checkin_date": "2023-05-18",
                        "checkout_date": "2023-05-20",
                        "rate_plan_id": data["rate_plan_1_id"],
                        "room_type_id": data["room_type_1_id"],
                    }
                ],
                "status": "cancelled",
            },
            "id": revision_cm_id,
            "type": "booking_revision",
        },
    )
    response = client.post(
        url,
        data={
            "event": "booking_cancellation",
            "payload": {
                "amount": "1240000",
                "arrival_date": "2023-05-18",
                "booking_id": booking_cm_id,
                "booking_revision_id": revision_cm_id,
                "booking_unique_id": "BDC-3611227021",
                "channel_id": "4f152895-b5c3-4c27-bc02-a99dc0f01072",
                "count_of_nights": 2,
                "count_of_rooms": 1,
                "currency": "VND",
                "customer_name": "Test Test",
                "live_feed_event_id": "cbadb500-151b-45a6-a44b-9b685e8bd802",
                "ota_code": "3611227021",
                "property_id": data["hotel_id"],
            },
            "property_id": data["hotel_id"],
            "timestamp": "2023-05-15T19:42:35.858695Z",
            "user_id": None,
        },
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert mocked_calculate_rates.call_count == 3
