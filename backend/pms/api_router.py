from django.conf import settings
from django.urls import path
from rest_framework.routers import DefaultRouter, SimpleRouter

from .views import (
    ChannexAvailabilityCallbackAPIView,
    HotelEmployeeModelViewSet,
    HotelModelViewSet,
    RoomModelViewSet,
    RoomTypeModelViewSet,
)

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register(
    "hotel",
    HotelModelViewSet,
    basename="hotel",
)
router.register(
    "hotel-employee",
    HotelEmployeeModelViewSet,
    basename="hotel-employee",
)
router.register(
    "room-type",
    RoomTypeModelViewSet,
    basename="room-type",
)
router.register(
    "room",
    RoomModelViewSet,
    basename="room",
)


app_name = "pms"
urlpatterns = router.urls
urlpatterns += [
    path(
        "channex/availability-callback/",
        ChannexAvailabilityCallbackAPIView.as_view(),
        name="channex-availability-callback",
    ),
]
