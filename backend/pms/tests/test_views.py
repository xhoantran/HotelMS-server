import pytest
from django.urls import reverse
from django.utils.http import urlencode
from rest_framework import status
from rest_framework.test import APIClient

from ..models import HotelAPIKey
from .factories import HotelFactory, RoomFactory, RoomTypeFactory


@pytest.mark.django_db
def test_hotel_employee_model_view_set_me_forbidden(admin, guest, get_api_client):
    url = reverse("pms:hotel-employee-me")
    admin_api_client = get_api_client(admin)
    response = admin_api_client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    guest_api_client = get_api_client(guest)
    response = guest_api_client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_hotel_employee_model_view_set_me(manager, staff, receptionist, get_api_client):
    url = reverse("pms:hotel-employee-me")
    manager_api_client = get_api_client(manager)
    response = manager_api_client.get(url)
    assert response.status_code == status.HTTP_200_OK

    staff_api_client = get_api_client(staff)
    response = staff_api_client.get(url)
    assert response.status_code == status.HTTP_200_OK

    receptionist_api_client = get_api_client(receptionist)
    response = receptionist_api_client.get(url)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_room_type_model_view_set_list(admin, manager, get_api_client):
    # Setup
    RoomTypeFactory.create_batch(10)
    RoomTypeFactory.create_batch(10, hotel=manager.hotel_employee.hotel)

    # Test
    url = reverse("pms:room-type-list")
    admin_api_client = get_api_client(admin)
    response = admin_api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 20
    manager_api_client = get_api_client(manager)
    response = manager_api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 10


@pytest.mark.django_db
def test_room_type_model_view_set_admin_create(admin, manager, get_api_client):
    # Setup
    url = reverse("pms:room-type-list")
    admin_api_client = get_api_client(admin)

    # Test
    response = admin_api_client.post(
        url,
        {
            "name": "Test",
            "hotel": manager.hotel_employee.hotel.id,
            "number_of_beds": 1,
            "base_rate": 100,
            "pms_id": "",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_room_type_model_view_set_manager_create(manager, get_api_client):
    # Setup
    url = reverse("pms:room-type-list")
    manager_api_client = get_api_client(manager)

    # Test
    response = manager_api_client.post(
        url,
        {
            "name": "Test",
            "hotel": manager.hotel_employee.hotel.id,
            "number_of_beds": 1,
            "base_rate": 100,
            "pms_id": "",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    fake_hotel = HotelFactory()
    response = manager_api_client.post(
        url,
        {
            "name": "Test",
            "hotel": fake_hotel.id,
            "number_of_beds": 1,
            "base_rate": 100,
            "pms_id": "",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_room_model_view_set_list(admin, manager, get_api_client):
    # Setup
    RoomFactory.create_batch(10)
    url = reverse("pms:room-list")
    admin_api_client = get_api_client(admin)

    # Test
    response = admin_api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 10


@pytest.mark.django_db
def test_room_model_view_set_admin_create(admin, get_api_client):
    # Setup
    url = reverse("pms:room-list")
    admin_api_client = get_api_client(admin)

    # Test
    room_type = RoomTypeFactory()
    response = admin_api_client.post(
        url,
        {
            "number": 1,
            "room_type": room_type.id,
        },
    )
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_room_model_view_set_manager_create(manager, get_api_client):
    # Setup
    url = reverse("pms:room-list")
    manager_api_client = get_api_client(manager)

    # Test
    room_type = RoomTypeFactory(hotel=manager.hotel_employee.hotel)
    response = manager_api_client.post(
        url,
        {
            "number": 1,
            "room_type": room_type.id,
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    room_type = RoomTypeFactory()
    response = manager_api_client.post(
        url,
        {
            "number": 2,
            "room_type": room_type.id,
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_channex_availability_callback_api_view(
    db,
    mocked_channex_validation,
    hotel_factory,
    room_type_factory,
):
    hotel = hotel_factory(channex=True)
    room_type = room_type_factory(hotel=hotel)
    HotelAPIKey.objects.get(hotel=hotel).delete()
    _, key = HotelAPIKey.objects.create_key(hotel=hotel, name="test")

    url = reverse("pms:channex-availability-callback")
    url = f"{url}?{urlencode({'room_type_uuid': room_type.uuid})}"
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Api-Key {key}")
    response = client.post(
        url,
        {"event": "ari", "payload": [], "user_id": None},
        format="json",
    )
    # No pms_id
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.post(
        url,
        {"event": "booking", "payload": [], "user_id": None},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = client.post(
        url,
        {
            "event": "ari",
            "payload": [],
            "user_id": "test",
            "property_id": hotel.pms_id,
        },
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
