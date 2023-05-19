from rest_framework import response, status, views

from backend.users.permissions import IsAdmin

from .models import CMHotelConnector, CMHotelConnectorAPIKey
from .permissions import HasCMHotelConnectorAPIKey
from .serializers import PreviewHotelSerializer, SetupHotelSerializer
from .tasks import setup_hotel_from_cm


class PreviewHotelAPIView(views.APIView):
    permission_classes = [IsAdmin]
    serializer_class = PreviewHotelSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        cm_data_serializer = CMHotelConnector(
            channel_manager=serializer.validated_data["channel_manager"],
            cm_id=serializer.validated_data["cm_id"],
            cm_api_key=serializer.validated_data["cm_api_key"],
        ).adapter.serialize_property_structure()

        return response.Response(cm_data_serializer.data, status=status.HTTP_200_OK)


class SetupHotelAPIView(views.APIView):
    permission_classes = [IsAdmin]
    serializer_class = SetupHotelSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        setup_hotel_from_cm.delay(
            channel_manager=serializer.validated_data["channel_manager"],
            cm_id=serializer.validated_data["cm_id"],
            cm_api_key=serializer.validated_data["cm_api_key"],
        )
        return response.Response(status=status.HTTP_200_OK)


class CMBookingWebhookTriggerAPIView(views.APIView):
    permission_classes = [HasCMHotelConnectorAPIKey]

    def post(self, request, *args, **kwargs):
        api_key = request.META["HTTP_AUTHORIZATION"].split()[1]
        cm_hotel_connector: CMHotelConnector = (
            CMHotelConnectorAPIKey.objects.get_from_key(api_key).cm_hotel_connector
        )

        cm_hotel_connector.adapter.save_booking_revision(data=request.data)
        return response.Response(status=status.HTTP_200_OK)
