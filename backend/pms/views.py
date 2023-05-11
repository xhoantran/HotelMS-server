from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters
from rest_framework import response, viewsets
from rest_framework.decorators import action

from backend.users.permissions import IsAdmin, IsEmployee, IsManager

from .filters import RoomTypeFilter
from .models import Hotel, HotelEmployee, Room, RoomType
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
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = RoomTypeFilter

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
