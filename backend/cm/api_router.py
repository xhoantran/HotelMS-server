from django.urls import path

from .views import (
    CMBookingWebhookTriggerAPIView,
    PreviewHotelAPIView,
    SetupHotelAPIView,
)

app_name = "cm"
urlpatterns = [
    path(
        "hotel/preview/",
        PreviewHotelAPIView.as_view(),
        name="hotel-preview",
    ),
    path(
        "hotel/setup/",
        SetupHotelAPIView.as_view(),
        name="hotel-setup",
    ),
    path(
        "webhook/booking/",
        CMBookingWebhookTriggerAPIView.as_view(),
        name="webhook-booking",
    ),
]
