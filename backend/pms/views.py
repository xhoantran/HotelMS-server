from django.contrib.auth import get_user_model
from rest_framework import generics, response, viewsets
from rest_framework.decorators import action

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


class HotelEmployeeModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdmin]
    queryset = HotelEmployee.objects.all()
    serializer_class = HotelEmployeeSerializer

    @action(detail=False, methods=["GET"], permission_classes=[IsEmployee])
    def me(self, request, *args, **kwargs):
        hotel_employee = request.user.hotel_employee
        serializer = self.get_serializer(hotel_employee)
        return response.Response(serializer.data)


class RoomTypeModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsManager | IsAdmin]
    serializer_class = RoomTypeSerializer

    def get_queryset(self):
        if self.request.user.role == User.UserRoleChoices.ADMIN:
            return RoomType.objects.all()
        return RoomType.objects.filter(hotel=self.request.user.hotel_employee.hotel)


class RoomModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsManager | IsAdmin]
    serializer_class = RoomSerializer

    def get_queryset(self):
        if self.request.user.role == User.UserRoleChoices.ADMIN:
            return Room.objects.all()
        return Room.objects.filter(hotel=self.request.user.hotel_employee.hotel)


class ChannexAvailabilityCallbackAPIView(generics.GenericAPIView):
    permission_classes = [HasHotelAPIKey]

    def post(self, request, *args, **kwargs):
        key = request.META["HTTP_AUTHORIZATION"].split()[1]
        try:
            hotel = HotelAPIKey.objects.get_from_key(key=key).hotel
            adapter = ChannexPMSAdapter(hotel)
            room_type_uuid = request.GET.get("room_type_uuid")

            if request.data.get("event") != "ari":
                return response.Response(status=400, data={"error": "Invalid event"})

            # If user_id is present, it means that the request is triggered
            # by a manual action in the Channex dashboard.
            if request.data.get("user_id", True):
                return response.Response(
                    status=200, data={"status": "Ignore manual trigger"}
                )

            # TODO: Change this to a celery task
            adapter.handle_availability_trigger(
                room_type_uuid, request.data.get("payload")
            )
            return response.Response(status=200)

        except HotelAPIKey.DoesNotExist:
            return response.Response(status=401, data={"error": "Invalid API key"})
        except Exception as e:
            return response.Response(status=500, data={"error": str(e)})
