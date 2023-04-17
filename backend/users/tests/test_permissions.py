import pytest
from rest_framework.test import APIRequestFactory

from ..permissions import (
    IsAdmin,
    IsEmployee,
    IsGuest,
    IsManager,
    IsReceptionist,
    IsStaff,
    ReadOnly,
)


@pytest.mark.django_db
def test_admin_permission(admin):
    request = APIRequestFactory().get("/")
    request.user = admin
    permission = IsAdmin()
    assert permission.has_permission(request, None) is True


@pytest.mark.django_db
def test_manager_permission(manager):
    request = APIRequestFactory().get("/")
    request.user = manager
    permission = IsManager()
    assert permission.has_permission(request, None) is True


@pytest.mark.django_db
def test_staff_permission(staff):
    request = APIRequestFactory().get("/")
    request.user = staff
    permission = IsStaff()
    assert permission.has_permission(request, None) is True


@pytest.mark.django_db
def test_receptionist_permission(receptionist):
    request = APIRequestFactory().get("/")
    request.user = receptionist
    permission = IsReceptionist()
    assert permission.has_permission(request, None) is True


@pytest.mark.django_db
def test_guest_permission(guest):
    request = APIRequestFactory().get("/")
    request.user = guest
    permission = IsGuest()
    assert permission.has_permission(request, None) is True


@pytest.mark.django_db
def test_employee_permission(
    admin,
    manager,
    staff,
    receptionist,
    guest,
):
    permission = IsEmployee()
    request = APIRequestFactory().get("/")

    request.user = admin
    assert permission.has_permission(request, None) is False

    request.user = manager
    assert permission.has_permission(request, None) is True

    request.user = staff
    assert permission.has_permission(request, None) is True

    request.user = receptionist
    assert permission.has_permission(request, None) is True

    request.user = guest
    assert permission.has_permission(request, None) is False

    request.user = None
    assert permission.has_permission(request, None) is False


@pytest.mark.django_db
def test_read_only():
    request = APIRequestFactory().get("/")
    permission = ReadOnly()
    assert permission.has_permission(request, None) is True

    permission = IsAdmin()
    assert permission.has_permission(request, None) is False

    permission = IsManager()
    assert permission.has_permission(request, None) is False

    permission = IsStaff()
    assert permission.has_permission(request, None) is False

    permission = IsReceptionist()
    assert permission.has_permission(request, None) is False

    permission = IsGuest()
    assert permission.has_permission(request, None) is False
