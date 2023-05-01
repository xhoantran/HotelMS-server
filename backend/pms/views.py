from typing import Any

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework import generics, response, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.request import Request
from rest_framework.response import Response

from backend.users.permissions import IsAdmin, IsEmployee, IsManager

from .adapter import ChannexPMSAdapter
from .models import Hotel, HotelAPIKey, HotelEmployee, Room, RoomType
from .permissions import HasHotelAPIKey
from .serializers import (
    HotelEmployeeSerializer,
    HotelSerializer,
    RoomSerializer,
    RoomTypeSerializer,
)

User = get_user_model()


class HotelModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdmin]
    queryset = Hotel.objects.all()
    serializer_class = HotelSerializer
    lookup_field = "uuid"

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            raise APIException(detail="Property with this external ID already exists")

    @action(detail=True, methods=["POST"], permission_classes=[IsAdmin])
    def sync(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        hotel: Hotel = self.get_object()
        if hotel.pms == Hotel.PMSChoices.CHANNEX:
            try:
                HotelAPIKey.objects.get(hotel=hotel).delete()
            except HotelAPIKey.DoesNotExist:
                pass
            _, api_key = HotelAPIKey.objects.create_key(hotel=hotel, name="API Key")
            hotel.adapter.sync_up(api_key=api_key)
            return Response(status=200)
        return Response(status=400)


class HotelEmployeeModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdmin]
    queryset = HotelEmployee.objects.all()
    serializer_class = HotelEmployeeSerializer
    lookup_field = "uuid"

    @action(detail=False, methods=["GET"], permission_classes=[IsEmployee])
    def me(self, request, *args, **kwargs):
        hotel_employee = request.user.hotel_employee
        serializer = self.get_serializer(hotel_employee)
        return response.Response(serializer.data)


class RoomTypeModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsManager | IsAdmin]
    serializer_class = RoomTypeSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        if self.request.user.role == User.UserRoleChoices.ADMIN:
            return RoomType.objects.all()
        return RoomType.objects.filter(hotel=self.request.user.hotel_employee.hotel)


class RoomModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsManager | IsAdmin]
    serializer_class = RoomSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        if self.request.user.role == User.UserRoleChoices.ADMIN:
            return Room.objects.all()
        return Room.objects.filter(hotel=self.request.user.hotel_employee.hotel)


class ChannexAvailabilityCallbackAPIView(generics.GenericAPIView):
    permission_classes = [HasHotelAPIKey]

    def post(self, request, *args, **kwargs):
        if request.data.get("event") != "ari":
            return response.Response(status=400, data={"error": "Invalid event"})

        try:
            key = request.META["HTTP_AUTHORIZATION"].split()[1]
            hotel = HotelAPIKey.objects.get_from_key(key=key).hotel
            if str(hotel.pms_id) != request.data.get("property_id"):
                return response.Response(
                    status=401, data={"error": "Invalid property_id"}
                )

            # If user_id is present, it means that the request is triggered
            # by a manual action in the Channex dashboard.
            if not request.data.get("user_id", True):
                ChannexPMSAdapter(hotel).handle_booked_ari_trigger(
                    room_type_uuid=request.GET.get("room_type_uuid"),
                    payload=request.data.get("payload"),
                )
            return response.Response(status=200)

        except HotelAPIKey.DoesNotExist:
            return response.Response(status=401, data={"error": "Invalid API key"})
        except Exception as e:
            return response.Response(status=500, data={"error": str(e)})
