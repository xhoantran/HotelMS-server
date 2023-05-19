import pytest
from django.urls import reverse
from rest_framework import status

from .factories import HotelFactory, RoomTypeFactory


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
def test_room_type_model_view_set_list_create(admin, manager, get_api_client):
    url = reverse("pms:room-type-list")
    admin_api_client = get_api_client(admin)
    manager_api_client = get_api_client(manager)

    # Test create
    response = admin_api_client.post(
        url,
        {
            "name": "Test",
            "hotel": manager.hotel_employee.hotel.uuid,
            "number_of_beds": 1,
            "base_rate": 100,
        },
    )
    assert response.status_code == status.HTTP_201_CREATED

    # Setup hotel not associated with manager
    RoomTypeFactory()

    # Test list
    response = admin_api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2
    response = manager_api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1


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
            "hotel": manager.hotel_employee.hotel.uuid,
            "number_of_beds": 1,
            "base_rate": 100,
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    fake_hotel = HotelFactory()
    response = manager_api_client.post(
        url,
        {
            "name": "Test",
            "hotel": fake_hotel.uuid,
            "number_of_beds": 1,
            "base_rate": 100,
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_rate_plan_model_view_set_list_create(
    admin, manager, get_api_client, rate_plan_factory
):
    url = reverse("pms:rate-plan-list")
    admin_api_client = get_api_client(admin)
    manager_api_client = get_api_client(manager)

    # Test create
    response = admin_api_client.post(
        url,
        {
            "name": "Test",
            "room_type": RoomTypeFactory(hotel=manager.hotel_employee.hotel).uuid,
        },
    )
    assert response.status_code == status.HTTP_201_CREATED

    # Setup rate plan not associated with manager
    rate_plan_factory()

    # Test list
    response = admin_api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2
    response = manager_api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1


@pytest.mark.django_db
def test_room_model_view_set_list(admin, get_api_client, room_factory):
    # Setup
    room_factory()
    url = reverse("pms:room-list")
    admin_api_client = get_api_client(admin)

    # Test
    response = admin_api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1


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
            "room_type": room_type.uuid,
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
            "room_type": room_type.uuid,
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    room_type = RoomTypeFactory()
    response = manager_api_client.post(
        url,
        {
            "number": 2,
            "room_type": room_type.uuid,
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
