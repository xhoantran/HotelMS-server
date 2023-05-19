from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from .views import (
    HotelEmployeeModelViewSet,
    HotelModelViewSet,
    RatePlanModelViewSet,
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
    "rate-plan",
    RatePlanModelViewSet,
    basename="rate-plan",
)
router.register(
    "room",
    RoomModelViewSet,
    basename="room",
)


app_name = "pms"
urlpatterns = router.urls
